import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    _src_dir = Path(__file__).resolve().parent
    _src = str(_src_dir)
    if _src not in sys.path:
        sys.path.insert(0, _src)

import ipaddress
import tkinter as tk
from tkinter import messagebox, ttk

from config import Config, get_app_root
from database import Database


class RemarkApp:

    def __init__(self, root, cfg=None):

        self.root = root
        self.root.title("Remark 登録")
        self.root.resizable(False, False)

        icon_file = get_app_root() / "icon.ico"
        if icon_file.exists():
            try:
                self.root.iconbitmap(str(icon_file))
            except tk.TclError:
                pass

        if cfg is None:
            cfg = Config()

        self.db = Database(cfg.db_file)

        self.mode_var = tk.StringVar(
            value="single"
        )

        main = ttk.Frame(
            root,
            padding=12
        )
        main.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        #
        # モード選択
        #
        mode_frame = ttk.LabelFrame(
            main,
            text="登録モード",
            padding=8
        )
        mode_frame.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        ttk.Radiobutton(
            mode_frame,
            text="個別（IP指定）",
            variable=self.mode_var,
            value="single",
            command=self._on_mode_change
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Radiobutton(
            mode_frame,
            text="範囲（一括）",
            variable=self.mode_var,
            value="range",
            command=self._on_mode_change
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(16, 0)
        )

        #
        # IP入力
        #
        ip_frame = ttk.LabelFrame(
            main,
            text="IPアドレス",
            padding=8
        )
        ip_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        ttk.Label(
            ip_frame,
            text="IP:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.single_ip_entry = ttk.Entry(
            ip_frame,
            width=36
        )
        self.single_ip_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0)
        )

        self.range_label_start = ttk.Label(
            ip_frame,
            text="開始:"
        )
        self.range_label_start.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(8, 0)
        )

        self.range_start_entry = ttk.Entry(
            ip_frame,
            width=36
        )
        self.range_start_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=(8, 0)
        )

        self.range_label_end = ttk.Label(
            ip_frame,
            text="終了:"
        )
        self.range_label_end.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(4, 0)
        )

        self.range_end_entry = ttk.Entry(
            ip_frame,
            width=36
        )
        self.range_end_entry.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(8, 0),
            pady=(4, 0)
        )

        ip_frame.columnconfigure(1, weight=1)

        #
        # Remark
        #
        remark_frame = ttk.LabelFrame(
            main,
            text="Remark",
            padding=8
        )
        remark_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(8, 0)
        )

        self.remark_entry = ttk.Entry(
            remark_frame,
            width=48
        )
        self.remark_entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        remark_frame.columnconfigure(0, weight=1)

        #
        # ボタン
        #
        btn_frame = ttk.Frame(main)
        btn_frame.grid(
            row=3,
            column=0,
            pady=(12, 0)
        )

        ttk.Button(
            btn_frame,
            text="登録",
            command=self._on_register
        ).grid(
            row=0,
            column=0,
            padx=(0, 8)
        )

        ttk.Button(
            btn_frame,
            text="クリア",
            command=self._on_clear
        ).grid(
            row=0,
            column=1
        )

        #
        # 結果表示
        #
        result_frame = ttk.LabelFrame(
            main,
            text="結果",
            padding=8
        )
        result_frame.grid(
            row=4,
            column=0,
            sticky="nsew",
            pady=(8, 0)
        )

        self.result_text = tk.Text(
            result_frame,
            width=52,
            height=8,
            state="disabled",
            wrap="word"
        )
        self.result_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = ttk.Scrollbar(
            result_frame,
            command=self.result_text.yview
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )
        self.result_text.configure(
            yscrollcommand=scrollbar.set
        )

        self._on_mode_change()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._on_close
        )

    def _on_mode_change(self):

        is_single = (
            self.mode_var.get() == "single"
        )

        if is_single:
            self.single_ip_entry.grid()
            self.range_label_start.grid_remove()
            self.range_start_entry.grid_remove()
            self.range_label_end.grid_remove()
            self.range_end_entry.grid_remove()
        else:
            self.single_ip_entry.grid_remove()
            self.range_label_start.grid()
            self.range_start_entry.grid()
            self.range_label_end.grid()
            self.range_end_entry.grid()

    def _log(self, message):

        self.result_text.configure(
            state="normal"
        )
        self.result_text.insert(
            "end",
            message + "\n"
        )
        self.result_text.see("end")
        self.result_text.configure(
            state="disabled"
        )

    def _clear_log(self):

        self.result_text.configure(
            state="normal"
        )
        self.result_text.delete(
            "1.0",
            "end"
        )
        self.result_text.configure(
            state="disabled"
        )

    def _on_clear(self):

        self.single_ip_entry.delete(0, "end")
        self.range_start_entry.delete(0, "end")
        self.range_end_entry.delete(0, "end")
        self.remark_entry.delete(0, "end")
        self._clear_log()

    def _validate_ip(self, ip_text):

        ip_text = ip_text.strip()

        if not ip_text:
            raise ValueError(
                "IPアドレスを入力してください。"
            )

        try:
            addr = ipaddress.ip_address(
                ip_text
            )
        except ValueError:
            raise ValueError(
                f"無効なIPアドレスです: {ip_text}"
            )

        return str(addr)

    def _resolve_targets(self):

        remark = self.remark_entry.get().strip()

        if self.mode_var.get() == "single":

            ip = self._validate_ip(
                self.single_ip_entry.get()
            )

            status = self.db.get_ip_status(ip)

            if not status:
                raise ValueError(
                    f"DBに存在しないIPです: {ip}"
                )

            return [status], remark

        start_ip = self._validate_ip(
            self.range_start_entry.get()
        )
        end_ip = self._validate_ip(
            self.range_end_entry.get()
        )

        rows, missing = (
            self.db.get_ips_by_index_range(
                start_ip,
                end_ip
            )
        )

        if missing:
            raise ValueError(
                "DBに存在しないIPです: "
                + ", ".join(missing)
            )

        if not rows:
            raise ValueError(
                "対象IPが見つかりません。"
            )

        targets = [
            {
                "ip": row[0],
                "last_reply": row[1],
            }
            for row in rows
        ]

        return targets, remark

    def _never_replied(self, targets):

        return [
            t["ip"]
            for t in targets
            if not t.get("last_reply")
        ]

    def _confirm_warning(
        self,
        never_replied
    ):

        preview_limit = 10
        preview = never_replied[:preview_limit]
        lines = "\n".join(preview)

        if len(never_replied) > preview_limit:
            lines += (
                f"\n... 他 {len(never_replied) - preview_limit} 件"
            )

        message = (
            f"PING応答の記録がないIPが "
            f"{len(never_replied)} 件あります。\n\n"
            f"{lines}\n\n"
            "このまま登録しますか？"
        )

        return messagebox.askyesno(
            "警告",
            message,
            icon="warning"
        )

    def _on_register(self):

        self._clear_log()

        try:
            targets, remark = (
                self._resolve_targets()
            )
        except ValueError as exc:
            messagebox.showerror(
                "入力エラー",
                str(exc)
            )
            self._log(f"ERROR: {exc}")
            return

        never_replied = self._never_replied(
            targets
        )

        if never_replied:
            self._log(
                "警告: PING未応答のIP "
                f"({len(never_replied)} 件)"
            )

            for ip in never_replied:
                self._log(f"  - {ip}")

            if not self._confirm_warning(
                never_replied
            ):
                self._log("登録をキャンセルしました。")
                return

        ips = [t["ip"] for t in targets]

        self.db.update_remarks(
            ips,
            remark
        )

        self._log(
            f"登録完了: {len(ips)} 件"
        )
        self._log(
            f"Remark: {remark or '(空)'}"
        )

        messagebox.showinfo(
            "完了",
            f"{len(ips)} 件の remark を登録しました。"
        )

    def _on_close(self):

        self.db.close()
        self.root.destroy()


def main():

    root = tk.Tk()
    root.withdraw()

    try:
        cfg = Config()
    except RuntimeError as exc:
        messagebox.showerror(
            "設定エラー",
            str(exc),
            parent=root,
        )
        root.destroy()
        return

    db_file = Path(cfg.db_file)

    db_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not db_file.exists():
        messagebox.showerror(
            "DBエラー",
            (
                "データベースが見つかりません。\n\n"
                f"DB={db_file}\n"
                f"NETWORK={cfg.network}\n"
                f"config.ini={cfg.ini_file}\n\n"
                "main.exe を先に実行すると、"
                "NETWORK に応じた DB が作成されます。"
            ),
            parent=root,
        )
        root.destroy()
        return

    root.deiconify()
    RemarkApp(root, cfg)
    root.mainloop()


if __name__ == "__main__":
    main()
