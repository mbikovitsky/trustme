# trustme
Helper script for Visual Studio 2015 offline installation

## Usage
The script is pretty much self-explanatory, and the config file
is pre-populated with the known VSIX packages bundled with
the Visual Studio 2015 installer. Just correct the paths, and you
should be okay.

For more information about the problem this script addresses,
see [here][1].

As for the external utilities used by the script:
- `makecert` and `pvk2pfx` can be obtained from the Windows Driver Kit.
  The easiest way is, probably, to get version 7.1.0 of the Kit (available
  from [here][2]), and extract the utilities from the ISO.
- `vsixsigntool` can be obtained from [here][3]. You can download the NuGet
  package directly from this page, and then manually extract the utility
  (remember that NuGet packages are simply ZIP archives).

Oh, and one final thing. Currently, the script is very verbose.
If you find that disturbing, edit the `LOG_LEVEL` global variable
inside.

That's it, and have fun!


[1]: http://stackoverflow.com/q/32590194/851560
[2]: https://msdn.microsoft.com/en-us/windows/hardware/hh852365
[3]: https://www.nuget.org/packages/Microsoft.VSSDK.Vsixsigntool
