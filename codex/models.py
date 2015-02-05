
import mongoengine as db
import textwrap
import hashlib
import ssdeep
from codex.config import ENCRYPTION_KEY
from itertools import cycle


ArchX86 = 'x86'
ArchX64 = 'x64'
ArchUnknown = 'unknown'

Architectures = (
    (ArchX86, 'x86'),
    (ArchX64, 'x64'),
    (ArchUnknown, 'Unknown')
)

SampleTypeLibrary = 'lib'
SampleTypeExecutable = 'exe'
SampleTypeDriver = 'driver'
SampleTypeUnknown = 'unknown'
SampleTypes = (
    (SampleTypeLibrary, 'Library'),
    (SampleTypeExecutable, "Executable"),
    (SampleTypeDriver, 'Driver'),
    (SampleTypeUnknown, 'Unknown')
)


def encrypt_blob(blob):
    return str(
        bytearray(
            [ord(k) ^ ord(v) for (k, v) in zip(blob, cycle(ENCRYPTION_KEY))]
        )
    )

def decrypt_blob(blob):
    return encrypt_blob(blob)


class Sample(db.Document):
    md5 = db.StringField(max_length=32)
    sha1 = db.StringField(max_length=40)
    sha256 = db.StringField(max_length=64)
    ssdeep = db.StringField()
    tags = db.ListField(db.StringField())
    original_name = db.StringField()
    namespace = db.StringField()
    notes = db.StringField()
    arch = db.StringField(choices=Architectures)
    sample_type = db.StringField(choices=SampleTypes)
    blob = db.FileField()

    def decrypt(self):
        return decrypt_blob(self.blob.read())

    @classmethod
    def get_or_create(cls, blob, **kwargs):
        found = False
        sample = None

        md5 = hashlib.md5(blob).hexdigest()
        sha1 = hashlib.sha1(blob).hexdigest()
        sha256 = hashlib.sha256(blob).hexdigest()
        ssd = ssdeep.hash(blob)

        try:
            for s in Sample.objects(sha256=sha256):
                if s.md5 == md5 and s.sha1 == sha1:
                    found = True
                    sample = s
                    break
        except:
            raise

        if not found:
            sample = Sample(
                sha256=sha256,
                md5=md5,
                sha1=sha1,
                ssdeep=ssd,
                tags=kwargs.get('tags', []),
                original_name=kwargs.get('original_name', ''),
                namespace=kwargs.get('namespace', ''),
                notes=kwargs.get('notes', ''),
                arch=kwargs.get('arch', ArchUnknown),
                sample_type=kwargs.get('sample_type', SampleTypeUnknown)
            )

        return (found, sample)

    def set_blob(self, blob):
        self.blob.put(encrypt_blob(blob),
                      content_type='application/octet-stream')
