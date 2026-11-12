"""Acquire pinned official source bytes; prefer verified local originals; execute no upstream code."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse
import hashlib
import shutil

COMMIT='d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e'
SOURCES={
 'MPEA_dataset.csv':('MPEA_dataset.csv','a4542498c5d5af66372d4c99abaeeaa5254a12fe'),
 '2018_data.csv':('2018_data/2018_data.csv','1724b87f4e82c6ee9abed9a97ab945e92f199f92'),
 '2019_data.csv':('2019_data/2019_data.csv','aee7d343837b5e6b75081443236784745ff93358'),
 'wos_query_refs.bib':('2019_data/wos_query_refs.bib','670023f068c89096d19e7a08f8dd4baffa78a643'),
 'UPSTREAM_README.md':('README.md','6098191a72f4603ff285bf2e163b73e71ac947ec'),
 'UPSTREAM_LICENSE':('LICENSE','261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64'),
 'process.ipynb':('process.ipynb','834650dea27f866042d5a87b2706374aef5cf47a'),
 'upstream_utils.py.txt':('utils.py','aff8cb5c9ad75c2ab76359644abac774751fe3d7')}

def verify(content,expected):
    blob=hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
    if blob!=expected:raise ValueError('Pinned official source content mismatch')

def acquire(root):
    directory=root/'data/citrine/raw';directory.mkdir(parents=True,exist_ok=True)
    for name,(path,expected) in SOURCES.items():
        destination=directory/name
        if destination.exists():verify(destination.read_bytes(),expected);continue
        local=root/name
        if name in ('MPEA_dataset.csv','2018_data.csv','2019_data.csv','wos_query_refs.bib') and local.exists():
            content=local.read_bytes()
        else:
            url=f'https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/{COMMIT}/{path}'
            with urlopen(url,timeout=30) as response:
                if urlparse(response.url).scheme!='https':raise ValueError('Non-HTTPS redirect')
                content=response.read(2_000_001)
                if len(content)>2_000_000:raise ValueError('Unexpected source size')
        verify(content,expected)
        with destination.open('xb') as handle:handle.write(content)
    print('All8 official source artifacts verified locally; no upstream scripts executed.')

if __name__=='__main__':acquire(Path(__file__).resolve().parents[1])
