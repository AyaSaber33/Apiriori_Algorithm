import pandas as pd
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from itertools import combinations
import threading


class RetailMinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Retail POS Association Miner - Problem 2")
        self.root.geometry("700x650")

        # --- Input Fields ---
        tk.Label(root, text="Minimum Support :", font=('Arial', 10, 'bold')).pack(pady=5)
        self.ent_sup = tk.Entry(root)
        self.ent_sup.insert(0, "0.009")
        self.ent_sup.pack()

        tk.Label(root, text="Minimum Confidence :", font=('Arial', 10, 'bold')).pack(pady=5)
        self.ent_conf = tk.Entry(root)
        self.ent_conf.insert(0, "0.01")
        self.ent_conf.pack()

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='indeterminate')
        self.progress.pack(pady=10)

        self.btn_run = tk.Button(root, text="Run Problem 2 Analysis", command=self.start_thread,
                                 bg="#2ecc71", fg="white", font=('Arial', 10, 'bold'), width=25)
        self.btn_run.pack(pady=10)

        self.txt_output = scrolledtext.ScrolledText(root, width=80, height=20)
        self.txt_output.pack(padx=10, pady=10)

    def start_thread(self):
        # Start the analysis in a separate thread so the GUI doesn't freeze
        self.btn_run.config(state=tk.DISABLED)
        self.progress.start()
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.insert(tk.END, "Processing... Please wait (check console for live updates).\n")

        thread = threading.Thread(target=self.process_data)
        thread.start()

    def process_data(self):
        try:
            data = pd.read_csv("Retail_pos_basket_data.csv")

            # Group items by order_id
            transactions = data.groupby('order_id')['product_name'].apply(set).tolist()
            num_trans = len(transactions)

            min_sup = float(self.ent_sup.get())
            min_conf = float(self.ent_conf.get())

            freq_itemsets, rules = self.run_apriori(transactions, min_sup, min_conf, num_trans)

            self.root.after(0, lambda: self.display_results(freq_itemsets, rules, num_trans))

        except FileNotFoundError:
            self.root.after(0, lambda: messagebox.showerror("Error", "Retail_pos_basket_data.csv not found!"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.stop_loading)

    def stop_loading(self):
        self.progress.stop()
        self.btn_run.config(state=tk.NORMAL)

    def run_apriori(self, transactions, min_sup, min_conf, num_trans):
        item_counts = {}
        for trans in transactions:
            for item in trans:
                item_counts[item] = item_counts.get(item, 0) + 1

        current_freq = {frozenset([item]): count / num_trans
                        for item, count in item_counts.items() if count / num_trans >= min_sup}

        all_freq = current_freq.copy()
        k = 2

        while current_freq:
            print(f"Analyzing {k}-item combinations...")
            prev_items = list(current_freq.keys())
            candidates = set()

            # Join Step
            for i in range(len(prev_items)):
                for j in range(i + 1, len(prev_items)):
                    union = prev_items[i] | prev_items[j]

                    if len(union) == k:
                        all_subsets_frequent = all(
                            frozenset(subset) in current_freq
                            for subset in combinations(union, k - 1)
                        )

                        if all_subsets_frequent:
                            candidates.add(union)

            # Count Step
            current_freq = {}
            for cand in candidates:
                count = sum(1 for trans in transactions if cand.issubset(trans))
                support = count / num_trans
                if support >= min_sup:
                    current_freq[cand] = support

            all_freq.update(current_freq)
            k += 1

        # Rule Generation
        rules = []
        for itemset, support in all_freq.items():
            if len(itemset) > 1:
                for size in range(1, len(itemset)):
                    for subset in combinations(itemset, size):

                        antecedent = frozenset(subset)
                        consequent = itemset - antecedent

                        confidence = support / all_freq[antecedent]

                        if confidence >= min_conf:
                            rules.append((antecedent, consequent, confidence, support))
        return all_freq, rules

    def display_results(self, freq_itemsets, rules, num_trans):
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.insert(tk.END, f"Total Transactions: {num_trans}\n")
        self.txt_output.insert(tk.END, "--- FREQUENT ITEMSETS ---\n")

        for itemset, sup in sorted(freq_itemsets.items(), key=lambda x: x[1], reverse=True):
            self.txt_output.insert(tk.END, f"Support {sup:.3f}: {list(itemset)}\n")

        self.txt_output.insert(tk.END, "\n--- ASSOCIATION RULES ---\n")
        if not rules:
            self.txt_output.insert(tk.END, "No rules found. Try lowering Support or Confidence.")
        else:
            for ant, cons, conf, sup in rules:
                self.txt_output.insert(tk.END, f"{list(ant)} -> {list(cons)} | Conf: {conf:.2f} | Sup: {sup:.2f}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = RetailMinerApp(root)
    root.mainloop()