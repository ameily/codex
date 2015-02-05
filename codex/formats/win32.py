

import pefile
from codex import models


def populate_sample(sample, blob):
    try:
        pe = pefile.PE(data=blob)
    except:
        return False

    try:
        # Determine sample type
        if pe.is_exe():
            sample.sample_type = models.SampleTypeExecutable
        elif pe.is_dll():
            sample.sample_type = models.SampleTypeLibrary
        elif pe.is_driver():
            sample.sample_type = models.SampleTypeDriver
        else:
            sample.sample_type = models.SampleTypeUnknown

        # Determine architecture
        if pe.OPTIONAL_HEADER.Magic == pefile.OPTIONAL_HEADER_MAGIC_PE:
            sample.arch = models.ArchX86
        elif pe.OPTIONAL_HEADER.Magic == pefile.OPTIONAL_HEADER_MAGIC_PE_PLUS:
            sample.arch = models.ArchX64
        else:
            sample.arch = models.ArchUnknown
    except:
        return False

    return True



