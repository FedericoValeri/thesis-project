# come import sys, ma permette di dare un nome agli argomenti della CLI
import argparse


def hello(a, b):
    print(f"La somma dei due numeri è: {a + b}")


if __name__ == "__main__":

    # Imposto una descrizione per lo script
    parser = argparse.ArgumentParser(
        description='Script usato per fare la somma.')

    # Imposto i due argomenti della  CLI con nome, tipo e valore di default
    parser.add_argument("--number", type=int, default=1)
    parser.add_argument("--valore2", type=int, default=2)

    # Eseguo il parsing degli argomenti
    args = parser.parse_args()
    # Li associo a due variabili
    a = args.number
    b = args.valore2
    hello(a, b)
