import pandas as pd

white_list_words = pd.read_csv("polls/rse_model/notebooks/white_list_words.csv")['word'].values


def condition(token):
    result = (token.is_digit  # token must be a digit \
              and len(token) == 4  # token must be of length 4
              and int(token.text) > 0  # Token must be above certain date
    )
    return result


# and tokens[token.i-1].shape[0]!=X
# and tokens[token.i-1] in before_context.values


def isDate(span, find_context=False, earliest=0):
    # type: (docs, Bool, int) -> object
    # We should be able to work this out with entities (any([t.label_ == "DATE" for t in doc.ents])
    dates = []
    for i, token in enumerate(span[0:]):
        if condition(token):
            """if span[i-1].text not in white_list_words:
                BL.append(span[i-1].text)
                return 'BL'"""
            current = []
            current.append((int(token.text)))

            # This part is for debug
            if find_context == True:
                if token.i != 0:
                    before = span[token.i - 1]
                else:
                    before = ' '
                """if token.i<len(tokens)-1:
                    after.append(tokens[token.i+1])"""
                current.append(before)
                # End of debug part

            dates.append(current)
    result = [date[0] for date in dates] if dates else False
    return result
