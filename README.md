# Personal Portfolio (Flask)

A portfolio site with project cards and a contact form that saves messages to SQLite.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Make it yours

- `app.py`: edit the `PROJECTS` and `SKILLS` lists
- `templates/index.html`: change the name and the About paragraph
- `static/style.css`: change colors in the `:root` block at the top
- `/messages`: see messages people sent you (remove or protect this route before going public)

## Structure

```
portfolio/
  app.py
  requirements.txt
  templates/  base.html, index.html, messages.html
  static/     style.css
```

## Ideas to extend it

- Add a light/dark mode toggle
- Email yourself when a message arrives
- Add a password to the `/messages` page
- Move projects into the database and add an admin form
