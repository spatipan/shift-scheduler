from datetime import datetime, timedelta


# Check special holiday
# TODO: add more special holiday yearly DUE DATE: 2023-12-31
thai_special_holiday = [
datetime(2023, 1, 2), # วันหยุดชดเชยปีใหม่
datetime(2023, 3, 6), # วันมาฆบูชา
datetime(2023, 4, 6), # วันจักรี
datetime(2023, 4, 13), # วันสงกรานต์
datetime(2023, 4, 14), # วันสงกรานต์
datetime(2023, 4, 17), # วันหยุดชดเชยสงกรานต์
datetime(2023, 5, 4), # วันฉัตรมงคล
datetime(2023, 5, 5), # วันฉัตรมงคล หยุดพิเศษ
datetime(2023, 5, 17), # วันพืชมงคล
datetime(2023, 6, 5), # วันหยุดชดเชย
datetime(2023, 7, 28), # วันเกิด ร.10
datetime(2023, 8, 1), # วันอาสาฬหบูชา
datetime(2023, 8, 2), # วันเข้าพรรษา
datetime(2023, 8, 14), # วันหยุดชดเชยวันแม่
datetime(2023, 10, 13), # วันสวรรคต ร.9
datetime(2023, 10, 23), # วันปิยมหาราช
datetime(2023, 12, 5), # วันพ่อ
datetime(2023, 12, 11), # วันหยุดชดเชยวันรัฐธรรมนูญ
]

# define function to get list of holiday
def get_holiday(year, month):

    num_days = (datetime(year, month+1, 1) - datetime(year, month, 1)).days
    date_list = [datetime(year, month, day) for day in range(1, num_days+1)]

    if year != 2023:
        raise ValueError("Only support year 2023")

    # Check weekend
    weekend = [date.weekday() in [5, 6] for date in date_list]

    # Combine all holiday
    holiday = [weekend[i] or date_list[i] in thai_special_holiday for i in range(len(date_list))]

    return holiday

no_morn_con_date = [
    datetime(2023, 3, 1),
    datetime(2023, 3, 8),
    datetime(2023, 3, 15),
    datetime(2023, 3, 22),
    datetime(2023, 3, 29)]


# define get morning conference day
# TODO : input no_morn_con_date
def get_morn_con_day(year, month, no_morn_con_date=no_morn_con_date):
    num_days = (datetime(year, month+1, 1) - datetime(year, month, 1)).days
    date_list = [datetime(year, month, day) for day in range(1, num_days+1)]

    # Check weekend
    weekend = [date.weekday() in [5, 6] for date in date_list]

    # Check holiday
    holiday = [weekend[i] or date_list[i] in thai_special_holiday for i in range(len(date_list))]

    # Combine all holiday
    no_morn_con_day = [holiday[i] or date_list[i] in no_morn_con_date for i in range(len(date_list))]

    morn_con_day = [not no_morn_con_day[i] for i in range(len(date_list))]

    return morn_con_day

# print(get_morn_con_day(2023, 3))



def negated_bounded_span(works, start, length):
    """Filters an isolated sub-sequence of variables assined to True.
  Extract the span of Boolean variables [start, start + length), negate them,
  and if there is variables to the left/right of this span, surround the span by
  them in non negated form.
  Args:
    works: a list of variables to extract the span from.
    start: the start to the span.
    length: the length of the span.
  Returns:
    a list of variables which conjunction will be false if the sub-list is
    assigned to True, and correctly bounded by variables assigned to False,
    or by the start or end of works.
  """
    sequence = []
    # Left border (start of works, or works[start - 1])
    if start > 0:
        sequence.append(works[start - 1])
    for i in range(length):
        sequence.append(works[start + i].Not())
    # Right border (end of works or works[start + length])
    if start + length < len(works):
        sequence.append(works[start + length])
    return sequence

def add_soft_sequence_constraint(model, works, hard_min, soft_min, min_cost,
                                 soft_max, hard_max, max_cost, prefix):
   
    cost_literals = []
    cost_coefficients = []

    # Forbid sequences that are too short.
    for length in range(1, hard_min):
        for start in range(len(works) - length + 1):
            model.AddBoolOr(negated_bounded_span(works, start, length))

    # Penalize sequences that are below the soft limit.
    if min_cost > 0:
        for length in range(hard_min, soft_min):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ': under_span(start=%i, length=%i)' % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # We filter exactly the sequence with a short length.
                # The penalty is proportional to the delta with soft_min.
                cost_coefficients.append(min_cost * (soft_min - length))

    # Penalize sequences that are above the soft limit.
    if max_cost > 0:
        for length in range(soft_max + 1, hard_max + 1):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ': over_span(start=%i, length=%i)' % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # Cost paid is max_cost * excess length.
                cost_coefficients.append(max_cost * (length - soft_max))

    # Just forbid any sequence of true variables with length hard_max + 1
    for start in range(len(works) - hard_max):
        model.AddBoolOr(
            [works[i].Not() for i in range(start, start + hard_max + 1)])
    return cost_literals, cost_coefficients

def add_soft_sum_constraint(model, works, hard_min, soft_min, min_cost,
                            soft_max, hard_max, max_cost, prefix):
    
    cost_variables = []
    cost_coefficients = []
    sum_var = model.NewIntVar(hard_min, hard_max, '')
    # This adds the hard constraints on the sum.
    model.Add(sum_var == sum(works))
    if soft_min > hard_min and min_cost > 0:
        delta = model.NewIntVar(-len(works), len(works), '')
        model.Add(delta == soft_min - sum_var)
        # TODO(user): Compare efficiency with only excess >= soft_min - sum_var.
        excess = model.NewIntVar(0, 7, prefix + ': under_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(min_cost)

    # Penalize sums above the soft_max target.
    if soft_max < hard_max and max_cost > 0:
        delta = model.NewIntVar(-7, 7, '')
        model.Add(delta == sum_var - soft_max)
        excess = model.NewIntVar(0, 7, prefix + ': over_sum')
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(max_cost)

    return cost_variables, cost_coefficients
