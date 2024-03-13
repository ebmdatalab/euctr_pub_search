# Cross-registration and results availability of trials registered on the EUCTR

This analysis was published, open access, in [BMJ Medicine](https://doi.org/10.1136/bmjmed-2023-000738) in January 2024. Please cite the manuscript when referencing the code.

A pre-registered protocol and other project materials are available on the [OSF](https://osf.io/r3vc5/).

## Repository Details

This is a Docker-ready repsoitory containing code and data for this project. Please consult [`DEVELOPERS.md`](DEVELOPERS.md) for instructions on 
how to run this study in a Docker environment. A Docker installation guide is available at [`INSTALLATION_GUIDE.md`](INSTALLATION_GUIDE.md)

### Key Directories

*data* - This contains all the data for the project that is needed to run the code, or is created by the code.

*lib* - This contains various helper functions for use in the analysis notebooks.

*notebooks* - This contains the jupyter notebooks for data processing and handling, the main analysis, figure creation, and the assessment of inter-searcher reliability.

## How to view the notebooks

Notebooks live in the `notebooks/` folder (with an `ipynb`
extension). You can most easily view them [on
nbviewer](https://nbviewer.jupyter.org/github/ebmdatalab/<repo>/tree/master/notebooks/),
though looking at them in Github should also work.

To do development work, you'll need to set up a local jupyter server
and git repository - see `DEVELOPERS.md` for more detail.
