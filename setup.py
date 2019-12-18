import setuptools 


setuptools.setup(
        name="pyomics", 
        version="1.0", 
        author="ByoRyn",
        packages=setuptools.find_packages(exclude=['*.tests']),
        zip_safe=True,
        py_modules=['easy_install'],
)
