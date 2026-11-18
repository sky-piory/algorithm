
pi = 3.141592653589793


# 부품 하나의 임피던스 계산
def get_impedance(kind, value, frequency):

    if kind == "R":
        return complex(value, 0)

    elif kind == "L":
        x = 2 * pi * frequency * value
        return complex(0, x)

    else:
        x = 1 / (2 * pi * frequency * value)
        return complex(0, -x)


# 회로 전체의 임피던스 계산
def calculate_circuit(groups, types, values, frequency):

    branch_impedances = []

    for group in groups:

        total = complex(0, 0)

        for i in group:
            z = get_impedance(types[i], values[i], frequency)
            total = total + z

        if abs(total) == 0:
            return complex(0, 0)

        branch_impedances.append(total)

    total_y = complex(0, 0)

    for z in branch_impedances:
        total_y = total_y + 1 / z

    if abs(total_y) == 0:
        return None

    return 1 / total_y


# 공진 주파수 탐색
def find_resonance(groups, types, values):

    has_L = 0
    has_C = 0

    for group in groups:
        for i in group:

            if types[i] == "L":
                has_L = 1

            elif types[i] == "C":
                has_C = 1

    if has_L == 0 or has_C == 0:
        return None

    low = 1
    high = 1000000

    ratio = (high / low) ** (1 / 100)

    previous_frequency = low

    previous_z = calculate_circuit(
        groups, types, values, low
    )

    if previous_z == None:
        return None

    previous_imag = previous_z.imag

    for step in range(1, 101):

        frequency = low * ratio ** step

        z = calculate_circuit(
            groups, types, values, frequency
        )

        if z == None:
            continue

        current_imag = z.imag

        if previous_imag * current_imag < 0:

            left = previous_frequency
            right = frequency
            left_imag = previous_imag

            for i in range(40):

                middle = (left * right) ** 0.5

                middle_z = calculate_circuit(
                    groups, types, values, middle
                )

                if middle_z == None:
                    break

                middle_imag = middle_z.imag

                if left_imag * middle_imag <= 0:
                    right = middle

                else:
                    left = middle
                    left_imag = middle_imag

            return (left * right) ** 0.5

        previous_frequency = frequency
        previous_imag = current_imag

    return None


# 공학 접두어 출력
def engineering(value, unit):

    display = abs(value)
    prefix = ""

    while display >= 1000 and prefix != "G":

        display = display / 1000

        if prefix == "":
            prefix = "k"
        elif prefix == "k":
            prefix = "M"
        elif prefix == "M":
            prefix = "G"

    while display < 1 and display > 0 and prefix != "p":

        display = display * 1000

        if prefix == "":
            prefix = "m"
        elif prefix == "m":
            prefix = "µ"
        elif prefix == "µ":
            prefix = "n"
        elif prefix == "n":
            prefix = "p"

    return format(display, ".2f") + " " + prefix + unit


# 가능한 회로 조합 탐색
def find_best_circuit(types, values, voltage,
                      frequency, goal, target):

    best_error = None
    best_groups = None
    best_value = None

    n = len(types)

    for mask in range(1, 2 ** n):

        selected = []

        for i in range(n):

            if mask & (1 << i):
                selected.append(i)

        # 한 회로에 최대 8개 부품 사용
        if len(selected) > 8:
            continue

        # 전체 직렬회로
        groups = [selected]

        candidates = [[groups, "직렬회로"]]

        # 전체 병렬회로
        groups = []

        for i in selected:
            groups.append([i])

        candidates.append([groups, "병렬회로"])

        # 두 개의 직렬 가지가 병렬로 연결된 회로
        for cut in range(1, len(selected)):

            first = selected[:cut]
            second = selected[cut:]

            groups = [first, second]

            candidates.append([groups, "직병렬회로"])

        # 후보 회로 비교
        for candidate in candidates:

            groups = candidate[0]
            circuit_type = candidate[1]

            if goal == 3:

                result = find_resonance(
                    groups, types, values
                )

                if result == None:
                    continue

            else:

                z = calculate_circuit(
                    groups, types, values, frequency
                )

                if z == None:
                    continue

                impedance = abs(z)

                if impedance == 0:
                    continue

                current = voltage / impedance

                if goal == 1:
                    result = current

                else:
                    result = impedance

            error = abs(result - target) / target

            if best_error == None or error < best_error:

                best_error = error
                best_groups = groups
                best_value = result
                best_type = circuit_type

    if best_groups == None:
        return None

    return [best_groups, best_type, best_value, best_error]


# 추천 회로 출력
def print_circuit(groups, names):

    print("\n===== 추천 회로도 =====")

    for b in range(len(groups)):

        line = "가지 " + str(b + 1) + ": "

        line = line + "[전원] -- "

        for i in groups[b]:
            line = line + names[i] + " -- "

        line = line + "[전원]"

        print(line)

    if len(groups) == 1:
        print("모든 부품이 직렬로 연결됩니다.")

    else:
        print("각 가지 내부는 직렬 연결입니다.")
        print("각 가지끼리는 병렬 연결입니다.")


# 메인 프로그램
print("===== 자동 전기회로 설계 도우미 =====")

print("\n===== 전압 입력 =====")

voltage = float(input("전압(V): "))

if voltage <= 0:

    print("전압은 0보다 커야 합니다.")

else:

    print("\n===== 설계 목표 =====")
    print("1. 목표 전류")
    print("2. 목표 임피던스")
    print("3. 목표 공진 주파수")

    goal = int(input("목표 선택: "))

    if goal < 1 or goal > 3:

        print("잘못된 목표입니다.")

    else:

        if goal == 1:

            target = float(input("목표 전류(A): "))
            frequency = float(input("주파수(Hz): "))

        elif goal == 2:

            target = float(input("목표 임피던스(Ω): "))
            frequency = float(input("주파수(Hz): "))

        else:

            target = float(input("목표 공진 주파수(Hz): "))
            frequency = 0

        if target <= 0 or (goal != 3 and frequency <= 0):

            print("입력값은 0보다 커야 합니다.")

        else:

            print("\n===== 부품 개수 입력 =====")

            rc = int(input("저항 개수(0~5): "))
            lc = int(input("인덕터 개수(0~5): "))
            cc = int(input("커패시터 개수(0~5): "))

            if rc < 0 or rc > 5 or lc < 0 or lc > 5 or cc < 0 or cc > 5:

                print("부품 개수가 잘못되었습니다.")

            elif rc + lc + cc == 0:

                print("부품을 하나 이상 입력해야 합니다.")

            else:

                names = []
                types = []
                values = []

                invalid = 0

                print("\n===== 부품 값 입력 =====")
                print("저항은 Ω, 인덕터는 H, 커패시터는 F로 입력합니다.")

                for kind in ("R", "L", "C"):

                    if kind == "R":
                        count = rc
                        unit = "Ω"

                    elif kind == "L":
                        count = lc
                        unit = "H"

                    else:
                        count = cc
                        unit = "F"

                    for i in range(count):

                        name = kind + str(i + 1)

                        value = float(
                            input(name + " 값(" + unit + "): ")
                        )

                        if value <= 0:
                            print("부품 값은 0보다 커야 합니다.")
                            invalid = 1

                        names.append(name)
                        types.append(kind)
                        values.append(value)

                if rc + lc + cc > 8:
                    print("\n현재 버전은 한 회로에 최대 8개 부품까지 탐색합니다.")

                if invalid == 1:

                    print("잘못된 입력이 있어 계산을 중단합니다.")

                else:

                    print("\n===== 자동 회로 탐색 중 =====")

                    result = find_best_circuit(
                        types,
                        values,
                        voltage,
                        frequency,
                        goal,
                        target
                    )

                    if result == None:

                        print("조건에 맞는 회로를 찾지 못했습니다.")

                    else:

                        groups = result[0]
                        circuit_type = result[1]
                        best_value = result[2]
                        error = result[3]

                        print("\n===== 최적 회로 추천 =====")

                        print("회로 종류:", circuit_type)

                        print_circuit(groups, names)

                        print("\n===== 계산 결과 =====")

                        if goal == 1:

                            print("목표 전류:", engineering(target, "A"))
                            print("추천 전류:", engineering(best_value, "A"))

                            z = calculate_circuit(
                                groups, types, values, frequency
                            )

                            print("합성 임피던스:", engineering(abs(z), "Ω"))

                        elif goal == 2:

                            print("목표 임피던스:", engineering(target, "Ω"))
                            print("추천 임피던스:", engineering(best_value, "Ω"))

                            z = calculate_circuit(
                                groups, types, values, frequency
                            )

                            print("회로 전류:", engineering(voltage / abs(z), "A"))

                        else:

                            print("목표 공진 주파수:", engineering(target, "Hz"))
                            print("추천 공진 주파수:", engineering(best_value, "Hz"))

                        print("목표와의 오차:", format(error * 100, ".2f"), "%")

                        print("\n===== 설계 완료 =====")
