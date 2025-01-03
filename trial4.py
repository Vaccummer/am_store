from am_store2.common_tools import *
d = {
    1:{2:3, 3:{4:5, 6:{7:{8:9}}}},
    2:2,
    3:{2:3, 3:6},
}

d_h = dicta.flatten_dict(d, max_depth=2)
d_u2 = dicta.unflatten_dict(d_h)
d_u = dicta.unflatten_dict(d_h)
print(d==d_u2)


