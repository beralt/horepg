from setuptools import setup, find_packages
setup(
    name = "HorEPG",
    version = "0.1",
    packages = find_packages(),
    scripts = ['horepgd.py', 'horxmltv.py'],
    install_requires = ['requests'],
    package_data = {
      'horepg': ['horepg.py', 'tvheadend.py', 'oorboekje.py', 'xmltvdoc.py']
    },
    author = "Beralt Meppelink",
    author_email = "beralt@beralt.nl",
    description = "Parser to transform data from Horizon and Oorboekje to the XMLTV format",
    license = "MIT",
    keywords = "epg xmltv",
)
