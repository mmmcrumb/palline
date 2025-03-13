import math, random
from PySide2 import QtCore, QtGui, QtWidgets

class SimulationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SimulationWidget, self).__init__(parent)
        self.setWindowTitle("Simulazione Rotazione - Collisione Continua")
        self.setFixedSize(600, 600)
        
        # Timer per aggiornare la simulazione (~50 fps)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateSimulation)
        self.timer.start(20)  # ogni 20 ms
        
        self.dt = 0.02           # intervallo di tempo (s)
        self.gravity = 800       # accelerazione di gravità (pixel/s²)
        self.omega = 2.0         # velocità angolare costante (rad/s)
        self.theta = 0.0         # angolo corrente di rotazione (rad)
        self.containerSize = 400 # lato del quadrato (pixel)
        self.halfSize = self.containerSize / 2
        
        self.ballRadius = 10     # raggio delle palline (pixel)
        self.restitution = 0.6   # coefficiente di restituzione base (0-1)
        self.restitution_randomness = 0.2  # variazione casuale del coefficiente (range 0-1)
        self.noise_strength = 10  # intensità del rumore per la simulazione
        
        self.balls = []          # lista per lo stato delle palline
        default_color = QtGui.QColor(150, 150, 150)
        for i in range(100):
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
        # Imposta 4 colori fissi: rosso, verde, blu e giallo
        obstacleColors = [
            QtGui.QColor(255, 0, 0),    # rosso
            QtGui.QColor(0, 255, 0),    # verde
            QtGui.QColor(0, 0, 255),    # blu
            QtGui.QColor(255, 255, 0)   # giallo
        ]
        # Nuove posizioni per i centri degli ostacoli
        centers = [(-50, -150), (30, -130), (-20, 70), (110, 150)]
        self.obstacles = []
        for i, (cx, cy) in enumerate(centers):
            rect = QtCore.QRectF(cx - self.obstacleSize/2, cy - self.obstacleSize/2,
                                 self.obstacleSize, self.obstacleSize)
            self.obstacles.append({'rect': rect, 'color': obstacleColors[i]})
    
    def clamp(self, val, minimum, maximum):
        return max(minimum, min(val, maximum))
    
    def sweptCircleVsAABB(self, p0, p1, r, rect):
        # Espande il rettangolo dei bordi dell'ostacolo di r (raggio della pallina)
        x_min = rect.left() - r
        x_max = rect.right() + r
        y_min = rect.top() - r
        y_max = rect.bottom() + r

        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()

        if dx == 0:
            t_entry_x = -float('inf')
            t_exit_x = float('inf')
        else:
            if dx > 0:
                t_entry_x = (x_min - p0.x()) / dx
                t_exit_x = (x_max - p0.x()) / dx
            else:
                t_entry_x = (x_max - p0.x()) / dx
                t_exit_x = (x_min - p0.x()) / dx

        if dy == 0:
            t_entry_y = -float('inf')
            t_exit_y = float('inf')
        else:
            if dy > 0:
                t_entry_y = (y_min - p0.y()) / dy
                t_exit_y = (y_max - p0.y()) / dy
            else:
                t_entry_y = (y_max - p0.y()) / dy
                t_exit_y = (y_min - p0.y()) / dy

        t_entry = max(t_entry_x, t_entry_y)
        t_exit = min(t_exit_x, t_exit_y)

        if t_entry > t_exit or t_exit < 0 or t_entry > 1:
            return None  # Nessuna collisione
        else:
            # Determina la normale in base all'asse di collisione
            if t_entry_x > t_entry_y:
                if dx < 0:
                    normal = QtCore.QPointF(1, 0)
                else:
                    normal = QtCore.QPointF(-1, 0)
            else:
                if dy < 0:
                    normal = QtCore.QPointF(0, 1)
                else:
                    normal = QtCore.QPointF(0, -1)
            return t_entry, normal
    
    def updateSimulation(self):
        # Aggiorna l'angolo di rotazione del contenitore
        self.theta += self.omega * self.dt
        
        # Aggiorna posizione e velocità per ogni pallina
        for ball in self.balls:
            pos = ball['pos']
            vel = ball['vel']
            
            # Salva la posizione precedente per la collisione continua
            oldPos = QtCore.QPointF(pos)
            
            # Calcola la gravità nel sistema del contenitore:
            # g_local = R(-theta) * (0, gravity) = (gravity*sin(theta), gravity*cos(theta))
            g_x = self.gravity * math.sin(self.theta)
            g_y = self.gravity * math.cos(self.theta)
            
            # Accelerazione centrifuga: ω² * r (verso l'esterno)
            a_centrifugal = QtCore.QPointF(self.omega**2 * pos.x(), self.omega**2 * pos.y())
            
            # Accelerazione di Coriolis: 2ω * (vy, -vx)
            a_coriolis = QtCore.QPointF(2 * self.omega * vel.y(), -2 * self.omega * vel.x())
            
            # Accelerazione totale (somma delle forze)
            ax = g_x + a_centrifugal.x() + a_coriolis.x()
            ay = g_y + a_centrifugal.y() + a_coriolis.y()
            
            # Aggiorna velocità (integrazione semplice)
            vel.setX(vel.x() + ax * self.dt)
            vel.setY(vel.y() + ay * self.dt)
            
            # Aggiunge una componente casuale alla velocità (rumore)
            vel.setX(vel.x() + random.uniform(-self.noise_strength, self.noise_strength) * self.dt)
            vel.setY(vel.y() + random.uniform(-self.noise_strength, self.noise_strength) * self.dt)
            
            # Aggiorna posizione
            pos.setX(pos.x() + vel.x() * self.dt)
            pos.setY(pos.y() + vel.y() * self.dt)
            
            # Gestione collisioni con i bordi del contenitore (discreto)
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
            
            # Gestione collisione continua con gli ostacoli
            for obs in self.obstacles:
                result = self.sweptCircleVsAABB(oldPos, pos, self.ballRadius, obs['rect'])
                if result is not None:
                    t_entry, normal = result
                    # Calcola il punto di collisione lungo il tragitto
                    newX = oldPos.x() + (pos.x() - oldPos.x()) * t_entry
                    newY = oldPos.y() + (pos.y() - oldPos.y()) * t_entry
                    pos.setX(newX)
                    pos.setY(newY)
                    effective_restitution = self.clamp(self.restitution + random.uniform(-self.restitution_randomness, self.restitution_randomness), 0, 1)
                    dot = vel.x() * normal.x() + vel.y() * normal.y()
                    if dot < 0:
                        vel.setX(vel.x() - (1+effective_restitution)*dot*normal.x())
                        vel.setY(vel.y() - (1+effective_restitution)*dot*normal.y())
                    # La pallina assume il colore dell'ostacolo
                    ball['color'] = obs['color']
        
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Trasla l'origine al centro della finestra e applica la rotazione al contenitore
        center = QtCore.QPointF(self.width()/2, self.height()/2)
        painter.translate(center)
        painter.save()
        painter.rotate(math.degrees(self.theta))
        
        # Disegna il contenitore (quadrato)
        rect = QtCore.QRectF(-self.halfSize, -self.halfSize, self.containerSize, self.containerSize)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 3))
        painter.drawRect(rect)
        
        # Disegna gli ostacoli con i colori assegnati
        for obs in self.obstacles:
            painter.setBrush(QtGui.QBrush(obs['color']))
            painter.drawRect(obs['rect'])
        
        # Disegna le palline con il loro colore corrente (senza outline)
        painter.setPen(QtCore.Qt.NoPen)
        for ball in self.balls:
            pos = ball['pos']
            painter.setBrush(QtGui.QBrush(ball['color']))
            ballRect = QtCore.QRectF(pos.x()-self.ballRadius, pos.y()-self.ballRadius,
                                     self.ballRadius*2, self.ballRadius*2)
            painter.drawEllipse(ballRect)
        painter.restore()
        
        # Aggiunge il counter visivo nella parte alta dello schermo
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

def show_simulation_widget():
    global sim_widget
    try:
        if sim_widget is not None:
            sim_widget.close()
    except NameError:
        pass
    sim_widget = SimulationWidget()
    sim_widget.show()
    return sim_widget

show_simulation_widget()