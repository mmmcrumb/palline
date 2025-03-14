import math, random, sys
from PyQt5 import QtCore, QtGui, QtWidgets

class SimulationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SimulationWidget, self).__init__(parent)
        self.setWindowTitle("Simulazione Rotazione - Counter Colori (PyQt5)")
        self.setFixedSize(600, 600)
        
        # Timer per aggiornare la simulazione (~50 fps)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateSimulation)
        self.timer.start(20)  # ogni 20 ms
        
        self.dt = 0.02           # intervallo di tempo (s)
        self.gravity = 800       # accelerazione di gravità (pixel/s²)
        self.omega = 1.0         # velocità angolare costante (rad/s)
        self.theta = 0.0         # angolo corrente di rotazione (rad)
        self.containerSize = 400 # lato del quadrato (pixel)
        self.halfSize = self.containerSize / 2
        
        self.ballRadius = 10      # raggio delle palline (pixel)
        self.restitution = 0.6   # coefficiente di restituzione base (0-1)
        self.restitution_randomness = 0.2  # variazione casuale del coefficiente (range 0-1)
        self.noise_strength = 10 # intensità del rumore per la simulazione
        
        self.balls = []          # lista per lo stato delle palline
        default_color = QtGui.QColor(150, 150, 150)
        for i in range(1000):
            x = random.uniform(-self.halfSize + self.ballRadius, self.halfSize - self.ballRadius)
            y = random.uniform(-self.halfSize + self.ballRadius, self.halfSize - self.ballRadius)
            vx = random.uniform(-100, 100)
            vy = random.uniform(-100, 100)
            self.balls.append({
                'pos': QtCore.QPointF(x, y),
                'vel': QtCore.QPointF(vx, vy),
                'color': default_color
            })
        
        # Definisci 4 ostacoli (piccoli quadrati) ancorati al contenitore
        self.obstacleSize = 40
        obstacleColors = [
            QtGui.QColor(255, 0, 0),    # rosso
            QtGui.QColor(0, 255, 0),    # verde
            QtGui.QColor(0, 0, 255),    # blu
            QtGui.QColor(255, 255, 0)   # giallo
        ]
        centers = [(-50, -150), (30, -130), (-20, 70), (110, 150)]
        self.obstacles = []
        for i, (cx, cy) in enumerate(centers):
            rect = QtCore.QRectF(cx - self.obstacleSize/2, cy - self.obstacleSize/2,
                                 self.obstacleSize, self.obstacleSize)
            self.obstacles.append({'rect': rect, 'color': obstacleColors[i]})
    
    def clamp(self, val, minimum, maximum):
        return max(minimum, min(val, maximum))
    
    def updateSimulation(self):
        self.theta += self.omega * self.dt
        
        for ball in self.balls:
            pos = ball['pos']
            vel = ball['vel']
            
            # Calcola la gravità nel sistema del contenitore:
            g_x = self.gravity * math.sin(self.theta)
            g_y = self.gravity * math.cos(self.theta)
            
            # Accelerazione centrifuga
            a_centrifugal = QtCore.QPointF(self.omega**2 * pos.x(), self.omega**2 * pos.y())
            
            # Accelerazione di Coriolis
            a_coriolis = QtCore.QPointF(2 * self.omega * vel.y(), -2 * self.omega * vel.x())
            
            ax = g_x + a_centrifugal.x() + a_coriolis.x()
            ay = g_y + a_centrifugal.y() + a_coriolis.y()
            
            vel.setX(vel.x() + ax * self.dt)
            vel.setY(vel.y() + ay * self.dt)
            
            # Rumore
            vel.setX(vel.x() + random.uniform(-self.noise_strength, self.noise_strength) * self.dt)
            vel.setY(vel.y() + random.uniform(-self.noise_strength, self.noise_strength) * self.dt)
            
            pos.setX(pos.x() + vel.x() * self.dt)
            pos.setY(pos.y() + vel.y() * self.dt)
            
            # Collisione con i bordi del contenitore
            if pos.x() - self.ballRadius < -self.halfSize:
                pos.setX(-self.halfSize + self.ballRadius)
                effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                vel.setX(-vel.x() * effective_restitution)
            if pos.x() + self.ballRadius > self.halfSize:
                pos.setX(self.halfSize - self.ballRadius)
                effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                vel.setX(-vel.x() * effective_restitution)
            if pos.y() - self.ballRadius < -self.halfSize:
                pos.setY(-self.halfSize + self.ballRadius)
                effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                vel.setY(-vel.y() * effective_restitution)
            if pos.y() + self.ballRadius > self.halfSize:
                pos.setY(self.halfSize - self.ballRadius)
                effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                vel.setY(-vel.y() * effective_restitution)
            
            # Collisione con gli ostacoli (quadrati interni)
            for obs in self.obstacles:
                rect = obs['rect']
                cx = pos.x()
                cy = pos.y()
                closestX = min(max(cx, rect.left()), rect.right())
                closestY = min(max(cy, rect.top()), rect.bottom())
                dx = cx - closestX
                dy = cy - closestY
                dist_sq = dx*dx + dy*dy
                if dist_sq < self.ballRadius * self.ballRadius:
                    dist = math.sqrt(dist_sq) if dist_sq != 0 else 0.001
                    normal_x = dx / dist
                    normal_y = dy / dist
                    penetration = self.ballRadius - dist
                    pos.setX(pos.x() + normal_x * penetration)
                    pos.setY(pos.y() + normal_y * penetration)
                    dot = vel.x() * normal_x + vel.y() * normal_y
                    if dot < 0:
                        effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                        vel.setX(vel.x() - (1+effective_restitution)*dot*normal_x)
                        vel.setY(vel.y() - (1+effective_restitution)*dot*normal_y)
                    ball['color'] = obs['color']
        
        self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Disegna il contenitore con rotazione
        center = QtCore.QPointF(self.width()/2, self.height()/2)
        painter.translate(center)
        painter.save()
        painter.rotate(math.degrees(self.theta))
        
        rect = QtCore.QRectF(-self.halfSize, -self.halfSize, self.containerSize, self.containerSize)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 3))
        painter.drawRect(rect)
        
        for obs in self.obstacles:
            painter.setBrush(QtGui.QBrush(obs['color']))
            painter.drawRect(obs['rect'])
        
        # Disegna le palline (senza outline)
        for ball in self.balls:
            pos = ball['pos']
            painter.setBrush(QtGui.QBrush(ball['color']))
            painter.setPen(QtCore.Qt.NoPen)
            ballRect = QtCore.QRectF(pos.x()-self.ballRadius, pos.y()-self.ballRadius,
                                     self.ballRadius*2, self.ballRadius*2)
            painter.drawEllipse(ballRect)
        painter.restore()
        
        # Disegna il counter
        painter.resetTransform()
        font = QtGui.QFont("Arial", 12)
        painter.setFont(font)
        counter = {"Rosso": 0, "Verde": 0, "Blu": 0, "Giallo": 0, "Grigio": 0}
        red   = QtGui.QColor(255, 0, 0)
        green = QtGui.QColor(0, 255, 0)
        blue  = QtGui.QColor(0, 0, 255)
        yellow= QtGui.QColor(255, 255, 0)
        grey  = QtGui.QColor(150, 150, 150)
        for ball in self.balls:
            c = ball['color']
            if c == red:
                counter["Rosso"] += 1
            elif c == green:
                counter["Verde"] += 1
            elif c == blue:
                counter["Blu"] += 1
            elif c == yellow:
                counter["Giallo"] += 1
            elif c == grey:
                counter["Grigio"] += 1
        
        x = 10
        y = 20
        textColors = {"Rosso": red, "Verde": green, "Blu": blue, "Giallo": yellow, "Grigio": grey}
        for key in ["Rosso", "Verde", "Blu", "Giallo", "Grigio"]:
            painter.setPen(QtGui.QPen(textColors[key]))
            text = f"{key}: {counter[key]}"
            painter.drawText(x, y, text)
            x += painter.fontMetrics().width(text) + 20

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = SimulationWidget()
    widget.show()
    sys.exit(app.exec_())
