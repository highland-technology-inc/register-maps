import io
import os.path
import sys
import jinja2
from functools import lru_cache
import importlib.resources

from . import textfn

######################################################################
# Resource management

__version__ = '0.0.4.dev8'

# Base path for resource files
_RSC = 'resource/'

_RESOURCE_BASE = importlib.resources.files(__package__ + '.resource')

def _strip_resource(x:str) -> str:
    """Return x, optionally stripping resource/ as a prefix.
    
    Returns resourcename
    """
    if x.startswith(_RSC):
        return x[len(_RSC):]
    return x

@lru_cache(64)
def resource_bytes(resourcename:str) -> bytes:
    """Get a package resource as binary data.
    
    resourcename starts with 'resource/' if the file is in the resource
    directory.
    """
    
    rsc = _RESOURCE_BASE / _strip_resource(resourcename)
    return rsc.read_bytes()
        
@lru_cache(64)
def resource_text(resourcename:str, encoding:str='utf-8', errors:str='strict') -> str:
    """Get a package resource as a text string.
    
    resourcename starts with 'resource/' if the file is in the resource
    directory.
    """
    
    rsc = _RESOURCE_BASE / _strip_resource(resourcename)
    with rsc.open('r', encoding=encoding, errors=errors) as f:
        data = f.read()
    return data

# Create a jinja2 template environment
jinja = jinja2.Environment(
    loader = jinja2.PackageLoader(__package__, "resource"),
    trim_blocks = True,
    lstrip_blocks = True
)
jinja.filters['reflow'] = textfn.reflow

@lru_cache(64)
def resource_template(resourcename:str) -> jinja2.Template:
    """Get a package resource as a Jinja template.
    
    Since all of our jinja resources are expected to be under resource/,
    if that is the first part of the resource name then it is ignored.
    """
    
    resourcename = _strip_resource(resourcename)
    return jinja.get_template(resourcename)

######################################################################
# Package-wide global variables.
    
ProgramGlobals = {
    'verbose' : False
}

def printverbose(*args, **kwargs):
    """Print to stderr if ProgramGlobals['verbose']."""
    
    if ProgramGlobals['verbose']:
        kwargs.setdefault('file', sys.stderr)
        print(*args, **kwargs)

######################################################################
# Output destinations

class _BaseOutputDestination:
    def open(self, *args, **kwargs):
        raise NotImplementedError
    
    @property
    def stream(self):
        raise NotImplementedError

class TextOutput(_BaseOutputDestination):
    def __init__(self, filehandle):
        self.stream = filehandle

class DirOutput(_BaseOutputDestination):
    def __init__(self, dir):
        self.dir = dir
        
    def open(self, filename, *args, **kwargs):
        fn = os.path.join(self.dir, filename)
        return TextOutput(open(fn, *args, **kwargs))
        
class StdOutput(_BaseOutputDestination):
    def open(self, *args, **kwargs):
        return self
        
    @property
    def stream(self):
        return sys.stdout
        
class StringOutput(_BaseOutputDestination):
    def __init__(self):
        self.stream = io.StringIO()
        
    @property
    def str(self):
        return self.stream.getvalue()

######################################################################
# Output class registration.
    
class _Outputs:
    def __init__(self):
        self._outputs = {}
        
    def register(self, kls):
        """Register an output class for the command-line tool.
        
        Args:
            kls: The class of an object to use.  The registered name will be
                taken from the :attr:`Visitor.outputname` member.
                
        Return:
            kls, so this can be used as a class decorator.
            
        """
        self._outputs[kls.outputname] = kls
        return kls
    
    def __iter__(self):
        """Iterate over all the registered outputs."""
        return iter(self._outputs.keys())
        
    def docs(self, output):
        """Get the documentation for an output by name.
        
        Args:
            output (str): Name of a registered output.
        
        Return:
            Long multi-line str of reSTructuredText.
        """
        return resource_text('resource/{}/README.rst'.format(output))
        
    def output(self, output):
        """Get the output class for an output by name.
        
        Args:
            output (str): Name of a registered output.
        
        Returns:
            Class that can iterate an HtiElement tree.
        """
        return self._outputs[output]
Outputs = _Outputs()

__all__ = [
    'Outputs',
    'printverbose', 'ProgramGlobals',
    'resource_bytes', 'resource_text', 'resource_template'
    '__version__'
]
