from tempfile import TemporaryDirectory, mkstemp
import os
import subprocess
import re


class WikiTextConverter:
    """Uses pdxparse to convert game code to wikitext.

    pdxparse has to be in the path so that it can be called by this class.
    """

    def to_wikitext(self, country_scope=None, province_scope=None, modifiers=None):
        """calls pdxparse to convert the values of the parameter dicts from strings in pdxscript to wikitext. the dicts are modified in place

            most of the slowness of this function is the overhead from calling pdxparse
            and letting it parse the normal game files, so it is best to only call it once
            with everything which needs to be converted
        """
        with TemporaryDirectory() as tmpfolder:
            inputfolder = tmpfolder + '/in'
            os.mkdir(inputfolder)
            outputfolder = tmpfolder + '/output'
            self._replace_values_by_filenames(inputfolder, country_scope)
            self._replace_values_by_filenames(inputfolder, province_scope)
            self._replace_values_by_filenames(inputfolder, modifiers)
            pdxparse_arguments = ['pdxparse', '-e']
            if country_scope:
                for file in country_scope.values():
                    pdxparse_arguments.append('-c')
                    pdxparse_arguments.append(file)
            if province_scope:
                for file in province_scope.values():
                    pdxparse_arguments.append('-s')
                    pdxparse_arguments.append(file)
            if modifiers:
                for file in modifiers.values():
                    pdxparse_arguments.append('-m')
                    pdxparse_arguments.append(file)

            subprocess.run(pdxparse_arguments, check=True, cwd=tmpfolder)

            self._replace_filenames_with_values(outputfolder, country_scope)
            self._replace_filenames_with_values(outputfolder, province_scope)
            self._replace_filenames_with_values(outputfolder, modifiers)

    def add_indent(self, wikilist):
        return re.sub(r'^\*', '**', wikilist, flags=re.MULTILINE)

    def remove_indent(self, wikilist):
        return re.sub(r'^\*[\s]*', '', wikilist, flags=re.MULTILINE)

    def _create_temp_file(self, folder, contents):
        fp, filename = mkstemp(suffix='.txt', dir=folder)
        with os.fdopen(fp, mode='w') as file:
            file.write(contents)
        return filename

    def _readfile(self, filename):
        with open(filename) as file:
            return file.read()

    def remove_surrounding_brackets(self, string):
        """ remove {} from around a string

            this is needed, because ck2utils has no way of getting the inner code of a section
         """
        match = re.match(r'^[\s]*{(.*)}[\s]*$', string, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return string

    def _replace_values_by_filenames(self, folder, dictionary):
        if dictionary:
            for key in dictionary:
                value = self.remove_surrounding_brackets(dictionary[key])
                dictionary[key] = self._create_temp_file(folder, value)

    def _replace_filenames_with_values(self, folder, dictionary):
        if dictionary:
            for key in dictionary:
                dictionary[key] = self._readfile(folder + dictionary[key] + '/' + os.path.basename(dictionary[key]))
