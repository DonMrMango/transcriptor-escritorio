"""
Setup para instalación de transcriptor con pip
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leer README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='transcriptor-groq',
    version='1.0.0',
    author='Grupo Lada Technologies',
    author_email='contacto@grupolada.com',
    description='Librería de transcripción de audio/video con Groq Whisper',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/grupolada/transcriptor',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.9',
        ],
    },
    keywords='transcription audio video groq whisper speech-to-text ai',
    project_urls={
        'Bug Reports': 'https://github.com/grupolada/transcriptor/issues',
        'Source': 'https://github.com/grupolada/transcriptor',
        'Documentation': 'https://github.com/grupolada/transcriptor/blob/main/README.md',
    },
)
