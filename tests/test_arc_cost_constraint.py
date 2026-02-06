from optimise.routing.constraints.arc_cost import _combine_time_matrix


def test_combine_time_matrix_uses_walking_for_short_distances():
    time_matrix = [[0, 100], [100, 0]]
    haversine = [[0, 50], [50, 0]]  # meters
    combined = _combine_time_matrix(time_matrix, haversine, threshold=100)

    assert combined[0][1] < time_matrix[0][1]
    assert combined[1][0] < time_matrix[1][0]
