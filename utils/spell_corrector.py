from symspellpy.symspellpy import SymSpell, Verbosity
import os

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

# Load the default English frequency dictionary (optional but helps)
base_dict = os.path.join(os.path.dirname(__file__), "frequency_dictionary_en_82_765.txt")
if os.path.exists(base_dict):
    sym_spell.load_dictionary(base_dict, term_index=0, count_index=1)

# Load your custom domain terms from file
custom_dict = os.path.join(os.path.dirname(__file__), "filtered_symspell_terms.txt")
if os.path.exists(custom_dict):
    with open(custom_dict, "r", encoding="utf-8") as f:
        for line in f:
            term = line.strip()
            if term:
                sym_spell.create_dictionary_entry(term.lower(), 1000)

def correct_text(input_text):
    suggestion = sym_spell.lookup(input_text.lower(), Verbosity.TOP, max_edit_distance=2)
    if suggestion:
        return suggestion[0].term

    # Word-by-word correction fallback
    corrected_words = []
    for word in input_text.lower().split():
        word_suggestion = sym_spell.lookup(word, Verbosity.TOP, max_edit_distance=2)
        corrected_words.append(word_suggestion[0].term if word_suggestion else word)

    return " ".join(corrected_words)
