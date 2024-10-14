#增量式PID
import matplotlib.pyplot as plt
import time
class PID():
    def __init__(self, dt, max, min, Kp, Ki, Kd):
        self.dt = dt  # 循环时长
        self.max = max  # 操作变量最大值
        self.min = min  # 操作变量最小值
        self.Kp = Kp  # 比例增益
        self.Ki = Ki  # 微分增益
        self.Kd = Kd  # 积分增益
        self.error = 0  # 当前误差
        self.error_1 = 0  #上次误差
        self.error_2 = 0  # 上上次误差
        self.pre_output = 0  #上次的输出值

    def calculate(self, setPoint, pv):
        # 其中 pv:process value 即过程值

        error = setPoint - pv  # 误差（设定值与实际值的差值）
        Pout = self.Kp * (error - self.error_1)  # 比例项 Kp * (e(t)-e(t-1))
        Iout = self.Ki * error  # 积分项 Ki * e(t)
        Dout = self.Kd * (error - 2*self.error_1 + self.error_2)  # 微分项 Kd * (e(t)-2*e(t-1)+e(t-2))
        output = Pout + Iout + Dout + self.pre_output  # 新的目标值  位置式PID：u(t) = Kp*(e(t)-e(t-1)) + Ki*e(t) + Kd*(e(t)-2*e(t-1)+e(t-2)) + u(t-1）

        if (output > self.max):
            output = self.max
        elif (output < self.min):
            output = self.min

        self.pre_output = output
        self.error_2 = self.error_1  #e(k-2) = e(k) ,进入下一次计算使用
        self.error_1 = error  # e(k-1) = e(k)
        return output


def time_pid(val=10):

    pid = PID(1, 10, -10, 0.3, 0.4, 0.06)
    setpoint = 60
    z = []
    for i in range(60):
        inc = pid.calculate(setpoint, val)    #新的目标值
        pwm_out = int(inc * 10)
        #print("val:%f inc:%f pwm_out:%d" % (val, inc, pwm_out))
        #time.sleep(1)
        z.append(val)
        val += inc
    #for t in range(len(z)):
    return z



if __name__ == "__main__":
    re = time_pid()
    for i in range(60):
        print(re[i])
        time.sleep(1)
#设置绘图风格
# plt.style.use('ggplot')
# plt.figure(figsize=(8, 6), dpi=80)
# plt.plot(t, z, color="blue", linewidth=1.0, linestyle="-")
# plt.xlabel('time (S)')
# plt.ylabel('Temp= (C)')
# plt.show()
