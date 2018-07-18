import itertools
import numpy as np
import shapely.geometry
import shapely.wkt
from datetime import datetime
import pytz
import calendar
from nexustiles.nexustiles import NexusTileService

def map(tile_in_spark):
    from nexustiles.nexustiles import NexusTileService
    import shapely.wkt

    (bounding_wkt, dataset, time_range) = tile_in_spark
    tile_service = NexusTileService()

    ds1_nexus_tiles = \
        tile_service.get_tiles_bounded_by_polygon(shapely.wkt.loads(bounding_wkt),
                                                  dataset,
                                                  time_range[0],
                                                  time_range[1],
                                                  rows=5000)
    if len(ds1_nexus_tiles) == 0:
        print 'get_tiles_bounded_by_polygon returned 0 tiles for dataset {} in time {} - {} for bounds {}'.format(dataset,time_range[0],time_range[1], bounding_wkt)
        return []

    # Create a dictionary mapping each time stamp to a list of tuples.
    # Each tuple has 2 elements, the index of a tile that contains the 
    # time stamp, and the index of the time stamp among all the time stamps
    # contained in that tile.
    tile_dict = {}
    for i in range(len(ds1_nexus_tiles)):
        tile = ds1_nexus_tiles[i]
        for j in range(len(tile.times)):
            t = tile.times[j]
            if t not in tile_dict:
                tile_dict[t] = []
            tile_dict[t].append((i,j))
                
    # Create an aggregate array with all the data and associated mask for 
    # each time stamp and an aggregate array with the latitude corresponding
    # to each data element.  Then compute the statistics, weighting each
    # data element by cos(latitude).
    stats_arr = []
    for timeinseconds in sorted(tile_dict.keys()):
        cur_tile_list = tile_dict[timeinseconds]
        if len(cur_tile_list) == 0:
            continue

        for i,j in cur_tile_list:
            ds1_nexus_tiles[i].data[j].mask = ds1_nexus_tiles[i].data[j].mask | (ds1_nexus_tiles[i].data[j].data < 0.)
        
        tile_data_agg = \
            np.ma.array(data=np.hstack([ds1_nexus_tiles[i].data[j].data.flatten()
                                        for i,j in cur_tile_list]),
                        mask=np.hstack([ds1_nexus_tiles[i].data[j].mask.flatten()
                                        for i,j in cur_tile_list]))
        lats_agg = np.hstack([np.repeat(ds1_nexus_tiles[i].latitudes,
                                        len(ds1_nexus_tiles[i].longitudes))
                              for i,j in cur_tile_list])
        if (len(tile_data_agg) == 0) or tile_data_agg.mask.all():
            continue
        else:
            data_min = np.ma.min(tile_data_agg)
            data_max = np.ma.max(tile_data_agg)
            daily_mean = \
                np.ma.average(tile_data_agg,
                              weights=np.cos(np.radians(lats_agg))).item()
            data_count = np.ma.count(tile_data_agg)
            data_std = np.ma.std(tile_data_agg)

        # Return Stats by day
        stat = {
            'min': data_min,
            'max': data_max,
            'mean': daily_mean,
            'cnt': data_count,
            'std': data_std,
            'time': int(timeinseconds)
        }
        stats_arr.append(stat)
    return stats_arr

def get_min_max_date(tile_service, ds=None):
    min_date = pytz.timezone('UTC').localize(
        datetime.utcfromtimestamp(tile_service.get_min_time([], ds=ds)))
    max_date = pytz.timezone('UTC').localize(
        datetime.utcfromtimestamp(tile_service.get_max_time([], ds=ds)))

    return min_date.date(), max_date.date()

def calculate_monthly_average(month=None, bounding_polygon_wkt=None, 
                              ds=None):
    EPOCH = pytz.timezone('UTC').localize(datetime(1970, 1, 1))
    tile_service = NexusTileService()
    min_date, max_date = get_min_max_date(tile_service, ds=ds)
    monthly_averages, monthly_counts = [], []
    monthly_mins, monthly_maxes = [], []
    bounding_polygon = shapely.wkt.loads(bounding_polygon_wkt)
    for year in range(min_date.year, max_date.year + 1):
        if (max_date.year - year) > 10:
            continue
        beginning_of_month = datetime(year, month, 1)
        end_of_month = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
        start = (pytz.UTC.localize(beginning_of_month) - EPOCH).total_seconds()
        end = (pytz.UTC.localize(end_of_month) - EPOCH).total_seconds()
        tile_stats = tile_service.find_tiles_in_polygon(bounding_polygon, ds, start, end, 
                                                              fl=('id,'
                                                                  'tile_avg_val_d,tile_count_i,'
                                                                  'tile_min_val_d,tile_max_val_d,'
                                                                  'tile_min_lat,tile_max_lat,'
                                                                  'tile_min_lon,tile_max_lon'),
                                                              fetch_data=False)
        if len(tile_stats) == 0:
            continue

        print('calculate_monthly_average: Got {} tiles'.format(len(tile_stats)))
        # Split list into tiles on the border of the bounding box and tiles completely inside the bounding box.
        border_tiles, inner_tiles = [], []
        for tile in tile_stats:
            inner_tiles.append(tile) if bounding_polygon.contains(shapely.geometry.box(tile.bbox.min_lon,
                                                                                       tile.bbox.min_lat,
                                                                                       tile.bbox.max_lon,
                                                                                       tile.bbox.max_lat)) else border_tiles.append(
                                                                                           tile)

        # We can use the stats of the inner tiles directly
        tile_means = [tile.tile_stats.mean for tile in inner_tiles]
        tile_mins = [tile.tile_stats.min for tile in inner_tiles]
        tile_maxes = [tile.tile_stats.max for tile in inner_tiles]
        tile_counts = [tile.tile_stats.count for tile in inner_tiles]

        # Border tiles need have the data loaded, masked, and stats recalculated
        border_tiles = list(tile_service.fetch_data_for_tiles(*border_tiles))
        border_tiles = tile_service.mask_tiles_to_polygon(bounding_polygon, border_tiles)
        for tile in border_tiles:
            tile.update_stats()
            tile_means.append(tile.tile_stats.mean)
            tile_mins.append(tile.tile_stats.min)
            tile_maxes.append(tile.tile_stats.max)
            tile_counts.append(tile.tile_stats.count)

        tile_means = np.array(tile_means)
        tile_mins = np.array(tile_mins)
        tile_maxes = np.array(tile_maxes)
        tile_counts = np.array(tile_counts)

        sum_tile_counts = np.sum(tile_counts) * 1.0
        
        monthly_averages += [np.average(tile_means, None, tile_counts / sum_tile_counts).item()]
        monthly_mins += [np.average(tile_mins, None, tile_counts / sum_tile_counts).item()]
        monthly_maxes += [np.average(tile_maxes, None, tile_counts / sum_tile_counts).item()]
        monthly_counts += [sum_tile_counts]

    count_sum = np.sum(monthly_counts) * 1.0
    weights = np.array(monthly_counts) / count_sum

    return np.average(monthly_averages, None, weights).item(), \
           np.average(monthly_averages, None, weights).item(), \
           np.average(monthly_averages, None, weights).item()

def calc(ds, bounding_polygon, start_time, end_time,
         apply_seasonal_cycle_filter, spark_nparts=1, sc=None):
    # Calculate partial time ranges for each Spark partition.
    time_divs = np.linspace(start_time, end_time, spark_nparts+1)
    time_ranges_part = np.array([time_divs[:-1], time_divs[1:]]).T

    # Create array of tuples containing all of the arguments the Spark 
    # mapper needs.
    nexus_tiles_spark = [(bounding_polygon.wkt, ds,
                          tuple(time_range_part))
                         for time_range_part in time_ranges_part]

    # Launch Spark computations
    rdd = sc.parallelize(nexus_tiles_spark, spark_nparts)
    results = rdd.map(map).collect()
    results = list(itertools.chain.from_iterable(results))
    results = sorted(results, key=lambda entry: entry["time"])

    if apply_seasonal_cycle_filter:
        print('Applying seasonal cycle filter...')
        # Precomputed climatology for bounding box from 
        # lon -150 to -140 and lat 45 to 50.
        clim = [(7.53947539438664, 7.53947539438664, 7.53947539438664), (7.10400350075431, 7.10400350075431, 7.10400350075431), (6.869168913155274, 6.869168913155274, 6.869168913155274), (6.954768193244048, 6.954768193244048, 6.954768193244048), (7.8822635146353734, 7.8822635146353734, 7.8822635146353734), (9.545773009292219, 9.545773009292219, 9.545773009292219), (12.030873415051925, 12.030873415051925, 12.030873415051925), (14.341431513590075, 14.341431513590075, 14.341431513590075), (14.464895314303316, 14.464895314303316, 14.464895314303316), (12.733453802522387, 12.733453802522387, 12.733453802522387), (10.263467662461972, 10.263467662461972, 10.263467662461972), (8.439042555228779, 8.439042555228779, 8.439042555228779)]
        # clim = [calculate_monthly_average(month, bounding_polygon.wkt, ds)
        #         for month in range(1,13)]
        for result in results:
            month = datetime.utcfromtimestamp(result['time']).month
            month_mean, month_max, month_min = clim[month-1]
            seasonal_mean = result['mean'] - month_mean
            seasonal_min = result['min'] - month_min
            seasonal_max = result['max'] - month_max
            result['meanSeasonal'] = seasonal_mean
            result['minSeasonal'] = seasonal_min
            result['maxSeasonal'] = seasonal_max

    return results

def main(sc):
    ds = 'AVHRR_OI_L4_GHRSST_NCEI'
    west = -150
    east = -140
    south = 45
    north = 50
    bounding_polygon = shapely.geometry.Polygon([(west, south), 
                                                 (east, south), 
                                                 (east, north), 
                                                 (west, north), 
                                                 (west, south)])
    start_time = 1262304000 # 01/01/2010
    end_time = 1514764799   # 12/31/2017
    apply_seasonal_cycle_filter = False
    spark_nparts = 8
    
    res = calc(ds, bounding_polygon, start_time, end_time, 
               apply_seasonal_cycle_filter, spark_nparts=spark_nparts, sc=sc)
    return res
