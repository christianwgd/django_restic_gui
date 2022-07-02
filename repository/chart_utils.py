import colorsys
from django.utils.translation import gettext_lazy as _
from repository.models import RepoSize


def repo_datasets(index, repo):

    # def color_code(index, opacity):
    #     h = ((index * 60) % 360) / 360.0
    #     l = s = 0.9
    #     r, g, b = colorsys.hsv_to_rgb(h, l, s)
    #     return "rgba(%d,%d,%d,%.1f)" % (int(r * 255), int(g * 255), int(b * 255), opacity)

    # fg = color_code(index, 1.0)
    # bg = color_code(index, 0.1)
    fg = "#007bff"
    bg = "#007bff"

    datasets = [{
        'label': str(_('size [GB]')),
        'yAxisID': 'y1',
        'fill': False,
        'pointRadius': 2.0,
        'borderColor': fg,
        'pointBackgroundColor': fg,
        'backgroundColor': bg,
        'data': [],
    }, {
        'label': str(_('K files')),
        'yAxisID': 'y2',
        'fill': False,
        'pointRadius': 2.0,
        'borderColor': fg,
        'borderDash': [1, 1],
        'pointBackgroundColor': fg,
        'backgroundColor': bg,
        'data': [],
    }]

    queryset = RepoSize.objects.filter(repo__pk=repo.pk)

    # https://www.chartjs.org/docs/latest/axes/cartesian/time.html#time-units
    time_unit = 'day'

    for row in queryset:
        datasets[0]['data'].append({
            'x': row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'y': row.size/float(1 << 30)
        })
        datasets[1]['data'].append({
            'x': row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'y': row.file_count / 1000
        })

    return datasets, time_unit
