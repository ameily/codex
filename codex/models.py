
import mongoengine as db
import textwrap
from codex.config import ENCRYPTION_KEY




class Sample(db.Document):
    md5_digest = db.BinaryField(max_bytes=16)
    sha1_digest = db.BinaryField(max_bytes=20)
    sha256_digest = db.BinaryField(max_bytes=32)
    ssdeep = db.StringField()
    tags = db.ListField(db.StringField())
    original_name = db.StringField()
    namespace = db.StringField()
    notes = db.String()
    blob = db.FileField()

    @classmethod
    def hash_to_digest(cls, hash):
        return bytes([int(c, 16) for c in textwrap.wrap(hash, 2)])

    @property
    def md5(self):
        if not hasattr(self, '_md5'):
            self._md5 = ["{:02x}".format(b) for b in self.md5_digest]
        return self._md5

    @property
    def sha1(self):
        if not hasattr(self, '_sha1'):
            self._sha1 = ["{:02x}".format(b) for b in self.sha1_digest]
        return self._sha1

    @property
    def sha256(self):
        if not hasattr(self, '_sha256'):
            self._sha256 = ["{:02x}".format(b) for b in self.sha256_digest]
        return self._sha256

    def decrypt(self):
        data = self.blob.read()
        return bytes([k ^ v for (k, v) in zip(data, cycle(ENCRYPTION_KEY))])

    @classmethod
    def encrypt(cls, data):
        return bytes([k ^ v for (k, v) in zip(data, cycle(ENCRYPTION_KEY))])

