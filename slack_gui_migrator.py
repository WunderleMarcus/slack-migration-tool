import json
import os
import time
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime
import emoji

def post_text_message(token, channel_id, text, thread_ts=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'channel': channel_id,
        'text': text
    }
    if thread_ts and thread_ts != '':
        payload['thread_ts'] = thread_ts
    r = requests.post('https://slack.com/api/chat.postMessage', headers=headers, json=payload)
    return r.ok, r.text

def upload_file(token, channel_id, filepath, title='Datei', thread_ts=None):
    if not os.path.isfile(filepath):
        return False, f"Datei nicht gefunden: {filepath}"

    with open(filepath, 'rb') as file_content:
        data = {
            'channels': channel_id,
            'title': title
        }
        if thread_ts:
            data['thread_ts'] = thread_ts
        response = requests.post(
            'https://slack.com/api/files.upload',
            headers={'Authorization': f'Bearer {token}'},
            files={'file': file_content},
            data=data
        )
    return response.ok, response.text

class SlackMigratorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Slack Channel Migrator")

        self.export_dir = tk.StringVar()
        self.token = tk.StringVar()
        self.channel_mapping = {}

        tk.Label(master, text="Slack Bot Token:").grid(row=0, column=0, sticky='e')
        tk.Entry(master, textvariable=self.token, width=50, show='*').grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Export-Ordner:").grid(row=1, column=0, sticky='e')
        tk.Entry(master, textvariable=self.export_dir, width=50).grid(row=1, column=1, padx=5)
        tk.Button(master, text="Durchsuchen", command=self.browse_folder).grid(row=1, column=2, padx=5)

        tk.Button(master, text="Channel-Mapping eingeben", command=self.prompt_channel_mapping).grid(row=2, column=1, pady=5)
        tk.Button(master, text="Migration starten", command=self.run_migration).grid(row=3, column=1, pady=5)

        self.log_area = scrolledtext.ScrolledText(master, width=80, height=20)
        self.log_area.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.export_dir.set(folder_selected)

    def log(self, msg):
        self.log_area.insert(tk.END, msg + '\n')
        self.log_area.see(tk.END)
        self.master.update()

    def prompt_channel_mapping(self):
        mapping_window = tk.Toplevel(self.master)
        mapping_window.title("Channel-Mapping")

        tk.Label(mapping_window, text="Channelname").grid(row=0, column=0)
        tk.Label(mapping_window, text="Slack Channel-ID").grid(row=0, column=1)

        entries = []
        try:
            json_files = [f for f in os.listdir(self.export_dir.get()) if f.endswith('.json') and f != 'users.json']
        except:
            json_files = []
        for i, fname in enumerate(json_files):
            channel_name = fname.replace('.json', '')
            tk.Label(mapping_window, text=channel_name).grid(row=i+1, column=0)
            var = tk.StringVar()
            entry = tk.Entry(mapping_window, textvariable=var, width=30)
            entry.grid(row=i+1, column=1)
            entries.append((channel_name, var))

        def save_mapping():
            for name, var in entries:
                self.channel_mapping[name] = var.get()
            mapping_window.destroy()

        tk.Button(mapping_window, text="Speichern", command=save_mapping).grid(row=len(entries)+1, column=1)

    def run_migration(self):
        export_dir = self.export_dir.get()
        token = self.token.get()

        if not export_dir or not token:
            messagebox.showerror("Fehler", "Bitte Slack-Token und Export-Ordner angeben.")
            return

        try:
            with open(os.path.join(export_dir, 'users.json'), 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            user_map = {u['id']: u.get('real_name') or u.get('name', 'Unbekannt') for u in user_data}
        except Exception as e:
            messagebox.showerror("Fehler beim Laden von users.json", str(e))
            return

        for fname in os.listdir(export_dir):
            if not fname.endswith('.json') or fname == 'users.json':
                continue

            channel_name = fname.replace('.json', '')
            channel_id = self.channel_mapping.get(channel_name)
            if not channel_id:
                self.log(f"⚠️ Kein Channel-ID für {channel_name}. Übersprungen.")
                continue

            self.log(f"🔄 Migriere: #{channel_name}")
            try:
                with open(os.path.join(export_dir, fname), 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except Exception as e:
                self.log(f"❌ Fehler beim Laden von {fname}: {e}")
                continue

            for msg in messages:
                user = msg.get('user', 'System')
                username = user_map.get(user, 'Unbekannt')
                text = emoji.emojize(msg.get('text', ''), language='alias')
                ts = float(msg.get('ts', 0))
                date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                full_msg = f"*{username}* am {date_str}:\n{text}"

                thread_ts = msg.get('thread_ts') if msg.get('thread_ts') != msg.get('ts') else None

                ok, result = post_text_message(token, channel_id, full_msg, thread_ts=thread_ts)
                if ok:
                    self.log(f"✅ Nachricht gepostet.")
                else:
                    self.log(f"❌ Fehler: {result}")

                for file_obj in msg.get('files', []):
                    filename = file_obj.get('name')
                    filepath = os.path.join(export_dir, 'files', filename)
                    ok, result = upload_file(token, channel_id, filepath, title=filename, thread_ts=thread_ts)
                    if ok:
                        self.log(f"📎 Datei hochgeladen: {filename}")
                    else:
                        self.log(f"❌ Datei-Fehler: {result}")

                time.sleep(1)

        self.log("\n🎉 Migration abgeschlossen.")

if __name__ == '__main__':
    root = tk.Tk()
    app = SlackMigratorApp(root)
    root.mainloop()
