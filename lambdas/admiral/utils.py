from dictionary import synonym, stopwords

def remove_noise(input_text, lem):
    words = input_text.lower().split()
    noise_free_words = [lem.lemmatize(word, "v") for word in words if word not in stopwords]
    result = []
    for each in noise_free_words:
        for word in synonym:
            if each in synonym[word]:
                result.append(word)
                break
        else:
            result.append(each)
    noise_free_text = " ".join(result)
    return map_commands(noise_free_text)
