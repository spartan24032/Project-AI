import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class SimulationControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.addedAgents = []
        self.pickupCoords = []
        self.dropoffCoords = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simulation Control')
        self.setGeometry(100, 100, 1200, 800)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: World Creation
        self.worldCreationTab = QWidget()
        self.tabs.addTab(self.worldCreationTab, "World Creation")
        self.initWorldCreationTab()
        # Tab 2: Simulation Control
        self.simulationControlTab = QWidget()
        self.tabs.addTab(self.simulationControlTab, "Simulation")
        self.initSimulationControlTab()
        # Tab 3: Charts and Data
        self.chartsDataTab = QWidget()
        self.tabs.addTab(self.chartsDataTab, "Charts and Data")
        self.initChartsDataTab()


    def initWorldCreationTab(self):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        randomSeedLayout = QHBoxLayout()
        randomSeedLabel = QLabel("Random Seed: ")
        self.randomSeedInput = QLineEdit(self)
        randomSeedLayout.addWidget(randomSeedLabel)
        randomSeedLayout.addWidget(self.randomSeedInput)
        randomSeedLayout.addStretch()
        layout.addLayout(randomSeedLayout)
        self.complexWorldCheck = QCheckBox("Use Complex_World2 memory space", self)
        layout.addWidget(self.complexWorldCheck)

        worldSizeLayout = QHBoxLayout()
        worldSizeLabel = QLabel("World Size:")
        self.worldSizeInput = QLineEdit(self)
        self.worldSizeInput.setPlaceholderText("e.g., 5 for a 5x5 grid")
        worldSizeLayout.addWidget(worldSizeLabel)
        worldSizeLayout.addWidget(self.worldSizeInput)
        layout.addLayout(worldSizeLayout)

        simulationModeLayout = QHBoxLayout()
        self.simulationModeBtn = QPushButton("Episode Based Sim", self)
        self.simulationModeBtn.clicked.connect(self.toggleSimulationMode)

        self.simulationModeLabel = QLabel(" Episodes: ")
        self.episodesOrStepsInput = QLineEdit(self)
        self.episodesOrStepsInput.setPlaceholderText("300")

        simulationModeLayout.addWidget(self.simulationModeBtn)
        simulationModeLayout.addWidget(self.simulationModeLabel)
        simulationModeLayout.addWidget(self.episodesOrStepsInput)
        layout.addLayout(simulationModeLayout)

        layout.addItem(QSpacerItem(50, 50))

        # Section for Adding and Configuring Agents
        self.agentLayout = QHBoxLayout()
        addAgentBtn = QPushButton("Add Agent", self)
        addAgentBtn.clicked.connect(self.addAgentToList)
        self.agentLayout.addWidget(addAgentBtn)

        deleteAgentBtn = QPushButton("Delete Agent", self)
        deleteAgentBtn.clicked.connect(self.deleteLastAgent)
        self.agentLayout.addWidget(deleteAgentBtn)

        self.startCoordInput = QLineEdit()
        self.startCoordInput.setPlaceholderText("Start (x,y)")
        self.agentLayout.addWidget(self.startCoordInput)

        self.policyCombo = QComboBox()
        self.policyCombo.addItems(["PGreedy", "PExploit", "PRandom"])
        self.agentLayout.addWidget(self.policyCombo)

        self.learningFunctionCombo = QComboBox()
        self.learningFunctionCombo.addItems(["SARSA", "Q-learning"])
        self.agentLayout.addWidget(self.learningFunctionCombo)
        layout.addLayout(self.agentLayout)

        # Area to display added agents
        self.addedAgentsDisplay = QLabel("Added Agents: None")
        layout.addWidget(self.addedAgentsDisplay)
        layout.addItem(QSpacerItem(50, 50))
        self.pickupDropoffLayout = QHBoxLayout()


        capacityInputLayout = QHBoxLayout()
        capacityInputL = QLabel("Capacity for Pickups & Dropoffs: ")
        self.capacityInput = QLineEdit(self)
        capacityInputLayout.addWidget(capacityInputL)
        capacityInputLayout.addWidget(self.capacityInput)
        layout.addLayout(capacityInputLayout)
        addPickupDropoffBtn = QPushButton(" Add Pickup/Dropoff ", self)
        addPickupDropoffBtn.clicked.connect(self.addPickupDropoffToList)
        self.pickupDropoffLayout.addWidget(addPickupDropoffBtn)
        deletePickupDropoffBtn = QPushButton(" Delete Pickup/Dropoff ", self)
        deletePickupDropoffBtn.clicked.connect(self.deleteLastPickupDropoff)
        self.pickupDropoffLayout.addWidget(deletePickupDropoffBtn)

        self.pickupInput = QLineEdit()
        self.pickupInput.setPlaceholderText("Pickup (x,y)")
        self.pickupDropoffLayout.addWidget(self.pickupInput)

        self.dropoffInput = QLineEdit()
        self.dropoffInput.setPlaceholderText("Dropoff (x,y)")
        self.pickupDropoffLayout.addWidget(self.dropoffInput)
        layout.addLayout(self.pickupDropoffLayout)

        # Area to display added pickup/dropoff pairs
        self.addedPickupDropoffDisplay = QLabel("Added Pickup/Dropoff Pairs: None")
        layout.addWidget(self.addedPickupDropoffDisplay)

        layout.addItem(QSpacerItem(50, 50))
        self.previewWorldBtn = QPushButton("Preview World", self)
        self.previewWorldBtn.clicked.connect(self.onPreviewWorldClicked)
        layout.addWidget(self.previewWorldBtn)
        self.worldPreviewLayout = QVBoxLayout()
        self.initBlankWorldPreview(5)
        layout.addLayout(self.worldPreviewLayout)

        createAndRunBtn = QPushButton("Create World and Run", self)
        createAndRunBtn.clicked.connect(self.onCreateAndRunClicked)
        layout.addWidget(createAndRunBtn)

        self.randomSeedInput.setMaximumWidth(200)
        self.simulationModeBtn.setMaximumWidth(200)
        self.worldCreationTab.setLayout(layout)

    def deleteLastAgent(self):
        if self.addedAgents:
            self.addedAgents.pop()
            self.updateAddedAgentsDisplay()
        else:
            self.addedAgentsDisplay.setText("Added Agents: None")

    def addPickupDropoffToList(self):
        pickupCoords = self.pickupInput.text()
        dropoffCoords = self.dropoffInput.text()

        if pickupCoords and dropoffCoords:
            self.pickupCoords.append(pickupCoords)
            self.dropoffCoords.append(dropoffCoords)
            self.updateAddedPickupDropoffDisplay()
            self.pickupInput.clear()
            self.dropoffInput.clear()

    def deleteLastPickupDropoff(self):
        if self.pickupCoords and self.dropoffCoords:
            self.pickupCoords.pop()
            self.dropoffCoords.pop()
            self.updateAddedPickupDropoffDisplay()
        else:
            self.addedPickupDropoffDisplay.setText("Added Pickup/Dropoff Pairs: None")

    def updateAddedPickupDropoffDisplay(self):
        if not self.pickupCoords or not self.dropoffCoords:
            self.addedPickupDropoffDisplay.setText("Added Pickup/Dropoff Pairs: None")
        else:
            pairsStr = "\n".join([f"Pickup: {pickup}, Dropoff: {dropoff}"
                                  for pickup, dropoff in zip(self.pickupCoords, self.dropoffCoords)])
            self.addedPickupDropoffDisplay.setText(f"Pickup/Dropoff Pairs:\n{pairsStr}")
            self.addedPickupDropoffDisplay.setStyleSheet("color: #293BFF")


    def initSimulationControlTab(self):
        layout = QGridLayout()

        # Simulation display area for images or text
        self.simulationDisplay = QTextEdit(self)
        self.simulationDisplay.setPlaceholderText("Simulation Display")
        self.simulationDisplay.setReadOnly(True)
        layout.addWidget(self.simulationDisplay, 0, 0, 1, 4)  # Span four columns for a wider display

        # Q-table display area
        self.qTableDisplay = QTextEdit(self)
        self.qTableDisplay.setPlaceholderText("Q-Table Display")
        self.qTableDisplay.setReadOnly(True)
        layout.addWidget(self.qTableDisplay, 0, 4, 1, 2)  # Next to the simulation display

        # Button to proceed to the next step
        self.nextBtn = QPushButton('Next', self)
        self.nextBtn.clicked.connect(self.onNextClicked)
        layout.addWidget(self.nextBtn, 1, 0)

        # Button to play continuously
        self.playBtn = QPushButton('Play', self)
        self.playBtn.clicked.connect(self.onPlayClicked)
        layout.addWidget(self.playBtn, 1, 1)

        # Button to pause autoplay
        self.pauseBtn = QPushButton('Pause', self)
        self.pauseBtn.clicked.connect(self.onPauseClicked)
        layout.addWidget(self.pauseBtn, 1, 2)

        # Input for skipping steps
        self.skipInput = QLineEdit(self)
        self.skipInput.setPlaceholderText('Enter steps to skip')
        layout.addWidget(self.skipInput, 1, 3)

        # Button to skip steps
        self.skipBtn = QPushButton('Skip', self)
        self.skipBtn.clicked.connect(self.onSkipClicked)
        layout.addWidget(self.skipBtn, 1, 4)

        # Slider for controlling autoplay speed
        self.speedSlider = QSlider(Qt.Horizontal)
        self.speedSlider.setMinimum(1)
        self.speedSlider.setMaximum(100)
        self.speedSlider.setValue(50)  # Default value

        # Label to display slider value
        self.speedValueLabel = QLabel("50")  # Initialize with default slider value
        self.speedSlider.valueChanged.connect(self.updateSpeedValue)  # Connect signal to slot

        # Layout adjustments to include the slider and its value label
        layout.addWidget(QLabel("Speed:"), 2, 0)
        layout.addWidget(self.speedSlider, 2, 1, 1, 2)
        layout.addWidget(self.speedValueLabel, 2, 3)  # Display the current speed value next to the slider

        self.simulationControlTab.setLayout(layout)

    def initChartsDataTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Visualization Will Be Here"))
        self.chartsDataTab.setLayout(layout)

    isEpisodeBased = True
    def toggleSimulationMode(self):
        if self.isEpisodeBased:
            self.simulationModeBtn.setText("Step Based Sim")
            self.simulationModeLabel.setText("Steps: ")
        else:
            self.simulationModeBtn.setText("Episode Based Sim")
            self.simulationModeLabel.setText("Episodes: ")
        self.isEpisodeBased = not self.isEpisodeBased

    def addAgentToList(self):
        startCoords = self.startCoordInput.text()
        if startCoords:
            policy = self.policyCombo.currentText()
            learningFunction = self.learningFunctionCombo.currentText()

            # Add the collected data to the list of added agents
            self.addedAgents.append((startCoords, policy, learningFunction))
            self.startCoordInput.clear()
            self.updateAddedAgentsDisplay()

    def updateAddedAgentsDisplay(self):
        if not self.addedAgents:
            self.addedAgentsDisplay.setText("Added Agents: None")
        else:
            agentsStr = "\n".join([f"Agent: {coords}, {policy}, {lf}"
                                   for coords, policy, lf in self.addedAgents])
            self.addedAgentsDisplay.setText(f"Added Agents:\n{agentsStr}")
            self.addedAgentsDisplay.setStyleSheet("color: #293BFF")

    def onNextClicked(self):
        print("Next clicked")

    def onPlayClicked(self):
        print("Play clicked")

    def onPauseClicked(self):
        print("Pause clicked")

    def onSkipClicked(self):
        steps = int(self.skipInput.text())
        print("Skipping to episode/step", steps)

    def updateSpeedValue(self, value):
        # Update the label with the current slider value
        self.speedValueLabel.setText(str(value))
        # Optionally, print the value to the console
        print(f"Slider Value: {value}")

    def onCreateAndRunClicked(self):
        random_seed = self.randomSeedInput.text()
        use_complex_world = self.complexWorldCheck.isChecked()
        print(f"Random Seed: {random_seed}")
        print(f"Use Complex World2: {use_complex_world}")


    def initBlankWorldPreview(self, size, agents=[], pickups=[], dropoffs=[]):
        self.clearLayout(self.worldPreviewLayout)

        gridContainer = QWidget()
        gridLayout = QGridLayout(gridContainer)
        gridLayout.setSpacing(0)

        for row in range(size):
            for col in range(size):
                cellLabel = QLabel(f"{row},{col}")
                cellLabel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
                cellLabel.setAlignment(Qt.AlignCenter)
                cellLabel.setStyleSheet("border: 1px solid black;")
                cellLabel.setFixedSize(80, 80)  # Increased size for better visibility and to fit the coordinate
                if (row, col) in agents:
                    print("Agent at", row, col)
                    cellLabel.setText("Agent")
                    cellLabel.setStyleSheet("color: blue; font-size: 20px; border: 1px solid black;")
                elif (row, col) in pickups:
                    cellLabel.setText("P")
                    cellLabel.setStyleSheet("color: green; font-size: 20px; border: 1px solid black;")
                elif (row, col) in dropoffs:
                    cellLabel.setText("D")
                    cellLabel.setStyleSheet("color: red; font-size: 20px; border: 1px solid black;")

                gridLayout.addWidget(cellLabel, row, col)
                gridLayout.addWidget(cellLabel, row, col)

        gridContainer.setLayout(gridLayout)
        gridContainer.setFixedSize(size * 100, size * 100)  # Adjust size based on number of squares and their size

        self.worldPreviewLayout.addWidget(gridContainer)

    def onPreviewWorldClicked(self):
        size = int(self.worldSizeInput.text())
        agentCoordStrings = [agentData[0] for agentData in self.addedAgents]
        agentCoords = [coord for coords in agentCoordStrings for coord in self.parseCoordinates(coords)]
        pickupCoords = [coord for coords in self.pickupCoords for coord in self.parseCoordinates(coords)]
        dropoffCoords = [coord for coords in self.dropoffCoords for coord in self.parseCoordinates(coords)]
        self.initBlankWorldPreview(size, agents=agentCoords, pickups=pickupCoords, dropoffs=dropoffCoords)

    def clearLayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def parseCoordinates(self, coordinateString):
        coordinates = []
        for part in coordinateString.replace(" ", "").strip().split("),("):
            clean_part = part.strip("()")
            if clean_part:
                try:
                    x, y = map(int, clean_part.split(","))
                    coordinates.append((x, y))
                except ValueError:
                    print(f"Invalid coordinate format: {clean_part}")
                    continue
        return coordinates

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = SimulationControl()
    mainWin.show()
    sys.exit(app.exec_())
