import pandas as pd
import tkinter as tk
from tkinter import messagebox, scrolledtext
from itertools import combinations
import threading


class SupermarketMiner:
    def __init__(self, root):
        self.root = root
        self.root.title("Problem 1: Supermarket Association Rules")
        self.root.geometry("800x700")

        # --- GUI INPUTS ---
        # Requirement 3: User must enter min support and min confidence at runtime
        tk.Label(root, text="Step 1: Min Support", font=('Arial', 10, 'bold')).pack(pady=5)
        self.ent_sup = tk.Entry(root)
        self.ent_sup.insert(0, "0.03")
        self.ent_sup.pack()

        tk.Label(root, text="Step 2: Min Confidence", font=('Arial', 10, 'bold')).pack(pady=5)
        self.ent_conf = tk.Entry(root)
        self.ent_conf.insert(0, "0.5")
        self.ent_conf.pack()

        self.btn_run = tk.Button(root, text="Analyze", command=self.start_task, bg="#e67e22",
                                 fg="white")
        self.btn_run.pack(pady=20)

        # Requirement 5: Output area for frequent itemsets and rules
        self.txt_output = scrolledtext.ScrolledText(root, width=95, height=30)
        self.txt_output.pack(padx=10, pady=10)

    def start_task(self):
        """Starts the analysis in a thread to keep the GUI responsive."""
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.insert(tk.END, "Preprocessing and Mining... Please wait.\n")
        threading.Thread(target=self.run_analysis).start()

    def run_analysis(self):
        try:
            # --- 1. DATA PREPROCESSING (Requirement 1) ---
            # Load data with specific encoding for retail descriptions
            df = pd.read_csv("supermarket_data.csv", encoding='ISO-8859-1')

            # Clean: Remove rows with empty descriptions
            df = df.dropna(subset=['Description'])

            # Requirement: Exclude all invoices starting with 'C' (returns)
            df['Invoice'] = df['Invoice'].astype(str)
            df = df[~df['Invoice'].str.startswith('C')]

            # Filter: Remove non-product items like POSTAGE
            df = df[df['Description'] != 'POSTAGE']

            # Requirement: Group items by Invoice number to create transactions (sets of items)
            transactions = df.groupby('Invoice')['Description'].apply(set).tolist()
            num_trans = len(transactions)

            # Get user inputs
            min_sup = float(self.ent_sup.get())
            min_conf = float(self.ent_conf.get())


            item_counts = {}
            for basket in transactions:
                for item in basket:
                    item_counts[item] = item_counts.get(item, 0) + 1

            current_freq = {frozenset([item]): count / num_trans
                            for item, count in item_counts.items()
                            if count / num_trans >= min_sup}

            all_frequent = current_freq.copy()
            k = 2

            while current_freq:
                items = list(current_freq.keys())
                candidates = set()

                # Join Step
                for i in range(len(items)):
                    for j in range(i + 1, len(items)):
                        union = items[i] | items[j]

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
                    count = sum(1 for basket in transactions if cand.issubset(basket))
                    support = count / num_trans
                    if support >= min_sup:
                        current_freq[cand] = support

                all_frequent.update(current_freq)
                k += 1

            rules = []
            rules = []
            for itemset, support in all_frequent.items():
                if len(itemset) > 1:
                    for size in range(1, len(itemset)):
                        for subset in combinations(itemset, size):

                            antecedent = frozenset(subset)
                            consequent = itemset - antecedent

                            if antecedent in all_frequent:
                                confidence = support / all_frequent[antecedent]

                                if confidence >= min_conf:
                                    rules.append((antecedent, consequent, confidence, support))

            self.root.after(0, lambda: self.display_results(all_frequent, rules, num_trans))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    def display_results(self, freq_itemsets, rules, total):
        self.txt_output.delete(1.0, tk.END)
        self.txt_output.insert(tk.END, f"Analyzed {total} valid transactions.\n")

        # 5.i List of frequent itemsets with support values
        self.txt_output.insert(tk.END, "\n" + "=" * 20 + " FREQUENT ITEMSETS " + "=" * 20 + "\n")
        if not freq_itemsets:
            self.txt_output.insert(tk.END, "No frequent itemsets found. Try a lower Support value.\n")
        else:
            # Sort by support descending
            for itemset, sup in sorted(freq_itemsets.items(), key=lambda x: x[1], reverse=True):
                self.txt_output.insert(tk.END, f"Support: {sup:.4f} | {list(itemset)}\n")

        # 5.ii List of association rules
        self.txt_output.insert(tk.END, "\n" + "=" * 20 + " ASSOCIATION RULES " + "=" * 20 + "\n")
        if not rules:
            self.txt_output.insert(tk.END, "No rules found. Try lower Confidence or Support.\n")
        else:
            for ant, cons, conf, sup in rules:
                self.txt_output.insert(tk.END, f"{list(ant)} -> {list(cons)} | Conf: {conf:.2f} | Sup: {sup:.4f}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = SupermarketMiner(root)
    root.mainloop()