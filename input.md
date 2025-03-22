## MODULE_NAME: real_blk

| REG_NAME: | my_reg1            |
| --------- | ------------------ |
| DESC:     | reg1 function desc |
| REG_TYPE: | RW                 |

| FIELDS:            | WIDTH | RESET | TYPE | DESC                                                     |
| ------------------ | ----- | ----- | ---- | -------------------------------------------------------- |
| imu_trigger_en     | 1     | 0x0   | RW   | trigger IMU                                              |
| depth_trigger_en   | 1     | 0x0   | RW   | trigger ir camera and 激光器                             |
| orb_trigger_en     | 1     | 0x0   | RW   | trigger orb camera enable for both                       |
| depth_pkt_word_num | 8     | 0x0   | RW   | Dword number in one depth packet                         |
| reserved           | 7     | 0x0   | RW   | use in future                                            |
| ir_frame_sel       | 1     | 0x0   | RW   | 1'b1: sel ir image for ref; 1'b0: sel 640*400 resolution |
| pkt_corner_num     | 8     | 0x0   | RW   | corner point number in one orb packet                    |

| REG_NAME: | my_reg2            |
| --------- | ------------------ |
| DESC:     | reg2 function desc |
| REG_TYPE: | RO                 |

| FIELDS: | WIDTH | RESET | TYPE | DESC          |
| ------- | ----- | ----- | ---- | ------------- |
| C2      | 2     | 0x3   | RO   | c2 field desc |
| A2      | 10    | 0x11  | RO   | a2 field desc |
| B2      | 20    | 0xff  | RO   | b2 field desc |

| REG_NAME: | my_reg3            |
| --------- | ------------------ |
| DESC:     | reg3 function desc |
| REG_TYPE: | RW                 |

| FIELDS:              | WIDTH | RESET  | TYPE | DESC                           |
|----------------------| ----- | ------ | ---- | ------------------------------ |
| gpif_read_pkt_length | 16    | 0xffff | RW   | pkt lenght when read from 3014 |