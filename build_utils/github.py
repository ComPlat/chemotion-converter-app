import os
import shutil
import tempfile
from pathlib import Path

import git

def reset_folder(path: Path) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def move_contents(src: Path, dst: Path) -> None:
    reset_folder(dst)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        shutil.move(s, d)

def load_client_build(dest: Path, repo = 'ComPlat/chemotion-converter-client', branch: str = 'master'):


    with tempfile.TemporaryDirectory() as t:
        # Clone into temporary dir
        git.Repo.clone_from(f'https://github.com/{repo}', t, branch=branch, depth=1)

        move_contents(Path(t) / 'build', dest)
    script = """
    <script>
      window.addEventListener("beforeunload", function () {
        navigator.sendBeacon('/shutdown');
      });
    </script>
    """

    # Inject the script before </body>
    for dirpath, dirnames, filenames in os.walk(dest):
        for filename in filenames:
            if filename == "index.html":
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    html = f.read()

                # Check if script already exists to avoid duplicates
                if script.strip() not in html:
                    html = html.replace("</body>", script + "\n</body>", 1)
                    html = html.replace("<title></title>", "<title>ChemConverter</title>", 1)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"Injected script into: {file_path}")
                else:
                    print(f"Script already exists in: {file_path}")