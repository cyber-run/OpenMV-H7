list1 = [['Name','Joseph', 'Anna', 'Lily'],['Age', 12, 32, 22],['Height', 5.7, 5.3, 4.9]]

with open('new.csv', 'w') as file:
    for i in list1:
        for j in i:
            file.write(str(j) + ',')
        file.write('\n')
