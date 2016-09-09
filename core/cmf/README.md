    The steps below need to be updated for Git/Bitbucket:

    Download and install the latest version of Eclipse - http://www.eclipse.org/
    Setup SVN - Download and install SVN subversion from within Eclipse
        Help -> Install New Software
        Select Collaboration then check all the SVN software and install
    Setup SVN Repositories 
        Open Eclipse -> Perspective -> SVN Repository Exploring
        In the SVN Repository Browser, select New Repository Location
        Enter the CMF repository location - http://216.243.97.229/svn/cmf - and your username and password for SVN
        Do the same for:
            http://216.243.97.229/svn/models
            http://216.243.97.229/svn/projects
            http://216.243.97.229/svn/third-party
            http://216.243.97.229/svn/ark
    Specify a local repository directory to store local copies of the projects.
        Create a system environment variable called REPOSITORY_DIR and set it equal to your local repository directory such as C:\projects\development
    You may need to specify a JAVA_HOME environment variable as well, such as C:\Program Files\Java\jdk1.7.0_13
    Get local copies of the following core project:
        cmf -> trunk -> right click & select check out as -> C:\projects\development\cmf
        models -> trunk -> right click & select check out as -> C:\projects\development\models
        projects -> trunk -> right click & select check out as -> C:\projects\development\projects
        third-party -> trunk -> right click & select check out as -> C:\projects\development\third-party
    Create eclipse projects for the core projects:
        Open Eclipse -> File -> Import -> select Existing Projects into Workspace
        Select root directory and browse to your local repository directory and select cmf
        Repeat for projects\build, third-party\logging-log4j-<version>, etc
    Building a project
        Each project should include a build.xml Ant script for building the project
        In Eclipse, right click on the script and go to Run As -> Ant build
        Once compiled, Eclipse should display the BUILD SUCCESSFUL message in the console.  This should output a JAR file (or multiple JAR files) to a release folder in the project directory.