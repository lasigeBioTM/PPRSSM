import sys

basename = sys.argv[1]

tp = 0
fp = 0
onecandidate = 0
onecandidate_tp = 0
total = 0


y_true = []
y_pred = []
pred_scores = []
with open("correct_{}".format(basename), 'r') as f:
    lines = f.read()
entities = lines.strip().split("==============================================")
for e in entities[1:]: # skip document line

    e = e.split("\n\n")
    #print(len(e[0]))

    #if len(e) == 3:
    correct_label = e[0].split("\t")[1].strip()
    y_true.append(correct_label)
    if len(e[0].strip().split("\n")) == 2:
        # print("one candidate")
        onecandidate += 1
        onecandidate_tp += 1
    #else:
    elines = e[1].split("\n")
    #print(elines)
    predicted = elines[0].split("(")[1].split(")")[0]
    y_pred.append(predicted)
    predicted_score = float(elines[0].split('\t')[1].split('>')[1])
    tp += 1
    total += 1
    #else:
    #    print(e)

with open("wrong_{}".format(basename), 'r') as f:
    lines = f.read()
entities = lines.strip().split("==============================================")
for e in entities[1:]:
    #print(e)
    e = e.strip().split("\n\n")
    #if len(e) == 3 and e[0][1] != "=":
    correct_label = e[0].strip().split("\t")[1]
    y_true.append(correct_label)
    if len(e[0].strip().split("\n")) == 2:
        # print("one candidate")
        onecandidate += 1
    elines = e[1].split("\n")
    #print(elines)
    predicted = elines[0].split("(")[1].split(")")[0]
    y_pred.append(predicted)
    predicted_score = float(elines[0].split('\t')[1].split('>')[1])
    #else:
    fp += 1
    total += 1
    #else:
    #    print(e)

all_classes = list(set(y_true).union(set(y_pred)))
correct_labels = []
for y in y_true:
    x = []
    for c in all_classes:
        if c == y:
            x.append(1)
        else:
            x.append(0)
    correct_labels.append(x)

predicted_labels = []
for y in y_pred:
    x = []
    for c in all_classes:
        if c == y:
            x.append(1)
        else:
            x.append(0)
    predicted_labels.append(x)


print("one candidate", onecandidate)
print("correct", tp)
print("wrong", fp)
print("total", total)
if total > 0:
    print("accuracy:", tp/total)
    if total - onecandidate > 0:
        print("accuracy (multiple candidates):", (tp-onecandidate_tp)/(total-onecandidate))
