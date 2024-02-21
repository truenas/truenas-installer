import os

import textwrap

import asyncio
import subprocess
import tempfile

__all__ = ["dialog", "dialog_checklist", "dialog_menu", "dialog_msgbox", "dialog_yesno"]


async def dialog(args, check=False):
    args = ["dialog"] + args

    process = await asyncio.create_subprocess_exec(*args, stderr=subprocess.PIPE)
    _, stderr = await process.communicate()

    stderr = stderr.decode("utf-8", "ignore")

    if check:
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, args, stderr=stderr)

    return subprocess.CompletedProcess(args, process.returncode, stderr=stderr)


async def dialog_checklist(title, text, items):
    result = await dialog(
        [
            "--clear",
            "--title", title,
            "--checklist", text, "20", "60", "0"
        ] +
        sum(
            [
                [k, v, "off"]
                for k, v in items.items()
            ],
            [],
        )
    )

    if result.returncode == 0:
        return result.stderr.split()
    else:
        return None


async def dialog_menu(title, items):
    result = await dialog(
        [
            "--clear",
            "--title", title,
            "--menu", "", "12", "73", "6"
        ] +
        sum(
            [
                [str(i), title]
                for i, title in enumerate(items.keys(), start=1)
            ],
            [],
        )
    )

    if result.returncode == 0:
        return await list(items.values())[int(result.stderr) - 1]()
    else:
        return None


async def dialog_msgbox(title, text):
    await dialog([
        "--clear",
        "--title", title,
        "--msgbox", text,
        str(4 + len(text.rstrip().splitlines())), "60",
    ])


async def dialog_password(title):
    with tempfile.NamedTemporaryFile("w") as dialogrc:
        dialogrc.write(textwrap.dedent("""\
            bindkey formfield TAB FORM_NEXT
            bindkey formfield DOWN FORM_NEXT
            bindkey formfield UP FORM_PREV
            bindkey formbox DOWN FORM_NEXT
            bindkey formbox TAB FORM_NEXT
            bindkey formbox UP FORM_PREV
        """))
        dialogrc.flush()

        while True:
            with tempfile.NamedTemporaryFile("r+") as output:
                fd = os.open(output.name, os.O_WRONLY)
                os.set_inheritable(fd, True)

                process = await asyncio.create_subprocess_exec(
                    *(
                        [
                            "dialog",
                            "--insecure",
                            "--output-fd", f"{fd}",
                            "--visit-items",
                            "--passwordform", title,
                            "10", "70", "0",
                            "Password:", "1", "10", "", "0", "30", "25", "50",
                            "Confirm Password:", "2", "10", "", "2", "30", "25", "50",
                        ]
                    ),
                    env=dict(os.environ, DIALOGRC=dialogrc.name),
                    pass_fds=(fd,),
                )
                await process.communicate()
                if process.returncode != 0:
                    return None

                passwords = [p.strip() for p in output.read().splitlines()]
                if len(passwords) != 2 or not passwords[0] or not passwords[1]:
                    await dialog_msgbox("Error", "Empty passwords are not allowed.")
                    continue
                elif passwords[0] != passwords[1]:
                    await dialog_msgbox("Error", "Passwords do not match.")
                    continue

                return passwords[0]


async def dialog_yesno(title, text) -> bool:
    result = await dialog([
        "--clear",
        "--title", title,
        "--yesno", text,
        "13", "74",
    ])
    return result.returncode == 0
