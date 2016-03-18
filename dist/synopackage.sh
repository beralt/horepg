#!/bin/sh

SRCS="../horepg.py ../horepgd.py ../tvheadend.py"
GPG=gpg2
GPG_OPTS="--ignore-time-conflict --ignore-valid-from --yes --batch"

SPK_IN="./horepg.spk"
SPK_OUT="./horepg.signed.spk"
SPK_EXTRACT_DIR="./SPK_UNTAR"
SPK_CATALL_OUT="./CATALL.dat"
SPK_SIG_FILE="syno_signature"
SPK_TOKEN_FILE="$SPK_EXTRACT_DIR/syno_signature.asc"
TIMESERVER="http://timestamp.synology.com/timestamp.php"

tar -cpzf syno/package.tgz --owner=root --group=root $SRCS
cd syno && tar -cvf ../horepg.spk --owner=root --group=root *

# FIXME: skipping signing for now
exit

# sign the package
$GPG $GPG_OPTS --list-secret-keys
export KEY_FPR=`$GPG $GPG_OPTS --list-secret-keys | egrep "^sec" | cut -d'/' -f2 | cut -d' ' -f1`
echo "Using SECRET_KEY $KEY_FPR"
# cleanup
rm -r "$SPK_EXTRACT_DIR" "$SPK_OUT" "$SPK_CATALL_OUT" "$SPK_SIG_FILE" "$SPK_TOKEN_FILE"
# extract
mkdir "$SPK_EXTRACT_DIR"
tar xf "$SPK_IN" -C "$SPK_EXTRACT_DIR"
cat `find $SPK_EXTRACT_DIR -type f | sort` > "$SPK_CATALL_OUT"
# sign
$GPG $GPG_OPTS --local-user $KEY_FPR --armor --detach-sign --output "$SPK_SIG_FILE" "$SPK_CATALL_OUT"
# token file
curl --form "file=@$SPK_SIG_FILE" "$TIMESERVER" > "$SPK_TOKEN_FILE"
# pack
tar -cf "$SPK_OUT" -C "$SPK_EXTRACT_DIR" `ls -1 $SPK_EXTRACT_DIR`
