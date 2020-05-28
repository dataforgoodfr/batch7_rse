import pandas as pd




def isDate(span, find_context=False, earliest=0):
    # type: (docs, Bool, int) -> object
    # We should be able to work this out with entities (any([t.label_ == "DATE" for t in doc.ents])
    dates = []
    for token in span:
        if (token.like_num
                and token.is_digit  # token must be a digit \
                and len(token) == 4  # token must be of length 4
                and int(token.text) > earliest  # Token must be above certain date
                and token.i != 0
                # and tokens[token.i-1].shape[0]!=X
                # and tokens[token.i-1] in before_context.values

        ):
            current = []
            current.append((int(token.text)))
            before = ' '
            if find_context == True:
                if token.i != 0:
                    before = tokens[token.i - 1]
                else:
                    before = ' '
                """if token.i<len(tokens)-1:
                    after.append(tokens[token.i+1])"""
            current.append(before)
            dates.append(current)
    result = dates if dates else False
    return result