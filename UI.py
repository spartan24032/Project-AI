import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import threading
import math
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import run_simulation
import random

# Example preset data
PRESET_AGENTS = [
    ("(0,2)", "PExploit", "Q-learning", "0.5", "0.3"),
    ("(2,2)", "PExploit", "Q-learning", "0.5", "0.3"),
    ("(4,2)", "PExploit", "Q-learning", "0.5", "0.3"),
]
PRESET_PICKUPS = ["(0,4)", "(1,3)", "(4,1)"]
PRESET_DROPOFFS = ["(0,0)", "(2,0)", "(3,4)"]
PRESET_WORLDSIZE = '5'

class SimulationControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.addedAgents = []
        self.pickupCoords = []
        self.dropoffCoords = []
        self.initUI()

        # Event to signal proceeding to the next step
        self.next_step_event = threading.Event()
        # Condition to manage autoplay and skip functionality
        self.autoplay_condition = threading.Condition()
        self.autoplay_enabled = False
        self.skip_to_step = None  # None means no skipping, otherwise store target step/episode
        self.masterskip = False

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

        presetBtn = QPushButton("Load Preset Data for Project", self)
        presetBtn.clicked.connect(self.loadPresetData)
        layout.addWidget(presetBtn)
        presetBtn.setMaximumWidth(300)
        layout.addItem(QSpacerItem(50, 50))

        randomSeedLayout = QHBoxLayout()
        randomSeedLabel = QLabel("Random Seed (leave blank for random seed): ")
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

        self.alphaInput = QLineEdit(self)
        self.alphaInput.setPlaceholderText("Alpha (0-1)")
        self.agentLayout.addWidget(self.alphaInput)

        # Input for gamma
        self.gammaInput = QLineEdit(self)
        self.gammaInput.setPlaceholderText("Gamma (0-1)")
        self.agentLayout.addWidget(self.gammaInput)

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
######
    def initSimulationControlTab(self):

        layout = QGridLayout()

        # Simulation display area for images or text
        self.worldStateContainer = QFrame(self)
        self.worldStateContainer.setFrameShape(QFrame.StyledPanel)
        self.worldStateGrid = QGridLayout()
        self.worldStateContainer.setLayout(self.worldStateGrid)

        layout.addWidget(self.worldStateContainer, 0, 0, 1, 4)
        self.simulationControlTab.setLayout(layout)
        # Initialize the grid with a default size (e.g., 5x5)
        self.initWorldStateGrid(5)

        # Q-table display area
        self.qTableDisplay = QTextEdit(self)
        self.qTableDisplay.setPlaceholderText("Q-Table Display")
        self.qTableDisplay.setReadOnly(True)
        layout.addWidget(self.qTableDisplay, 0, 4, 1, 1)  # Next to the simulation display

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
        self.skipInput.setPlaceholderText('steps/episodes to skip')
        self.skipInput.setMaximumWidth(250)
        layout.addWidget(self.skipInput, 1, 3)

        # Button to skip steps
        self.skipBtn = QPushButton('Skip', self)
        self.skipBtn.clicked.connect(self.onSkipClicked)
        self.skipBtn.setMaximumWidth(150)
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
######
    def initChartsDataTab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Visualization Will Be Here"))
        self.chartsDataTab.setLayout(layout)

######################################################################
    def initWorldStateGrid(self, size, agents=[], pickups=[], dropoffs=[]):
        # Clear existing grid layout
        self.clearLayout(self.worldStateGrid)

        for row in range(size):
            for col in range(size):
                cellLabel = QLabel(f"{row},{col}")
                cellLabel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
                cellLabel.setAlignment(Qt.AlignCenter)
                # Set style for better visibility
                cellLabel.setStyleSheet("border: 1px solid black;")
                cellLabel.setFixedSize(120, 120)

                # Display agents, pickups, and dropoffs with specific styles
                if (row, col) in agents:
                    cellLabel.setText("Agent")
                    cellLabel.setStyleSheet("color: blue; font-size: 20px; border: 1px solid black;")
                elif (row, col) in pickups:
                    cellLabel.setText("P")
                    cellLabel.setStyleSheet("color: green; font-size: 20px; border: 1px solid black;")
                elif (row, col) in dropoffs:
                    cellLabel.setText("D")
                    cellLabel.setStyleSheet("color: red; font-size: 20px; border: 1px solid black;")

                self.worldStateGrid.addWidget(cellLabel, row, col)

        # Optionally, adjust the size of the container if needed
        self.worldStateContainer.setFixedSize(size * 140, size * 140)

    def updateCurrentWorldDisplay(self, agents, env):
        size, actions, dropoffStorage, pickups, dropoffs, used_dropoffs = env.UIrenderVals()
        for row in range(size):
            for col in range(size):
                cell_label = self.worldStateGrid.itemAtPosition(row, col).widget()
                base_content = ' '
                cell_style = "QLabel { font-weight: bold; border: 1px solid black; "

                # Check for pickups and dropoffs
                if (row, col) in pickups:
                    base_content = f'P{pickups[(row, col)]}'
                    cell_style += "background-color: #3498db; color: white; "  # Light blue background
                elif (row, col) in dropoffs:
                    base_content = f'D{dropoffs[(row, col)]}'
                    cell_style += "background-color: #2ecc71; color: white; "  # Green background

                # Overlay agents
                agent_here = False
                for idx, agent in enumerate(agents):
                    agent_state, has_item = agent.get_state()
                    if agent_state == (row, col):
                        agent_mark = 'C' if has_item else 'A'
                        agent_id = str(idx)
                        agent_here = True
                        base_content = f"{agent_mark}{agent_id}"
                        cell_style += "background-color: #e74c3c; color: white; "  # Red background for agent
                        break

                if not agent_here:
                    cell_style += "background-color: white; color: black; "  # Default background

                cell_style += "}"

                # Find the QLabel in the current cell and update it
                cell_label.setText(base_content)
                cell_label.setStyleSheet(cell_style)

    def onNextClicked(self):
        # Signal the simulation to proceed to the next step
        print("next clicked, setting next_step_event")
        self.next_step_event.set()

    def onPlayClicked(self):
        with self.autoplay_condition:
            self.autoplay_enabled = True
            self.autoplay_condition.notify()  # Wake up the simulation if it's waiting
        self.next_step_event.set()

    def onPauseClicked(self):
        self.autoplay_enabled = False

    def onSkipClicked(self):
        self.skip_to_step = self.skipInput.text()
        # Optionally, signal to proceed if waiting for the next step
        self.next_step_event.set()

    def updateSpeedValue(self, value):
        # Update the label with the current slider value
        self.speedValueLabel.setText(str(value))
        print(f"Slider Value: {value}")

########

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
            alpha = self.alphaInput.text()
            gamma = self.gammaInput.text()
            policy = self.policyCombo.currentText()
            learningFunction = self.learningFunctionCombo.currentText()

            # Add the collected data to the list of added agents
            self.addedAgents.append((startCoords, policy, learningFunction, alpha, gamma))
            self.startCoordInput.clear()
            self.alphaInput.clear()
            self.gammaInput.clear()
            self.updateAddedAgentsDisplay()

    def updateAddedAgentsDisplay(self):
        if not self.addedAgents:
            self.addedAgentsDisplay.setText("Added Agents: None")
        else:
            agentsStr = "\n".join(
                [f"Start: {coords}, Policy: {policy}, Learning: {learning}, Alpha: {alpha}, Gamma: {gamma}"
                 for coords, policy, learning, alpha, gamma in self.addedAgents])
            self.addedAgentsDisplay.setText(f"Added Agents:\n{agentsStr}")
            self.addedAgentsDisplay.setStyleSheet("color: #293BFF")

    def onCreateAndRunClicked(self):

        # Assuming you have a method to parse coordinates from UI inputs
        size = int(self.worldSizeInput.text())
        try:
            randomSeed = int(self.randomSeedInput.text())
        except ValueError:
            randomSeed = random.random()

        # Setup environment
        random.seed(randomSeed)
        dropoffCapacity = int(self.capacityInput.text())
        initialDropoffInventory = 0
        pickups = {self.parseCoordinateToTuple(coord): dropoffCapacity for coord in self.pickupCoords}
        dropoffs = {self.parseCoordinateToTuple(coord): initialDropoffInventory for coord in self.dropoffCoords}

        env = GridWorld(size, pickups, dropoffs, dropoffCapacity)

        # Setup agents
        agentInstances = []
        for agentConfig in self.addedAgents:
            start_state = self.parseCoordinateToTuple(agentConfig[0])
            policy = {"PGreedy": PGreedy, "PExploit": PExploit, "PRandom": PRandom}.get(agentConfig[1])
            learning_algorithm = agentConfig[2]
            alpha = float(agentConfig[3]) if agentConfig[3] else 0.7
            gamma = float(agentConfig[4]) if agentConfig[4] else 0.8

            # Setup agents
            agentInstances = []
            for agentConfig in self.addedAgents:
                start_state = self.parseCoordinateToTuple(agentConfig[0])
                policy = {"PGreedy": PGreedy, "PExploit": PExploit, "PRandom": PRandom}.get(agentConfig[1])
                learning_algorithm = agentConfig[2]
                agent = Agent(
                    env.actions,
                    start_state=start_state,
                    policy=policy,
                    learning_algorithm=learning_algorithm,
                    alpha=alpha,
                    gamma=gamma
                )
                agentInstances.append(agent)

        complex_world2 = self.complexWorldCheck.isChecked()
        episode_based = self.isEpisodeBased
        r = int(self.episodesOrStepsInput.text())
        # Run simulation
        #run_simulation(agentInstances, env, sim_control, complex_world2, episode_based, r)
        # initWorldStateGrid(self, size, agents=[], pickups=[], dropoffs=[])
        self.initWorldStateGrid(size, agentInstances, pickups,dropoffs)
        # Create a thread to run the simulation without blocking the UI
        simulationThread = threading.Thread(target=run_simulation,
                                                 args=(agentInstances, env, self, complex_world2, episode_based, r))
        simulationThread.start()
        # Optionally, switch to the "Simulation Control" tab
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.simulationControlTab))

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

    def parseCoordinateToTuple(self, coordinateString):
        """Parses a single coordinate string '(x,y)' into a tuple (x, y)."""
        x, y = map(int, coordinateString.strip("()").split(","))
        return (x, y)

    def loadPresetData(self):
        # Clear existing data
        self.addedAgents.clear()
        self.pickupCoords.clear()
        self.dropoffCoords.clear()

        # Load preset agent data
        self.addedAgents.extend(PRESET_AGENTS)

        # Load preset pickup and dropoff locations
        self.pickupCoords.extend(PRESET_PICKUPS)
        self.dropoffCoords.extend(PRESET_DROPOFFS)
        self.worldSizeInput.setText(PRESET_WORLDSIZE)
        self.capacityInput.setText('5')
        self.episodesOrStepsInput.setText('30')
        self.randomSeedInput.setText('11')

        # Update the UI to reflect the preset data
        self.updateAddedAgentsDisplay()
        self.updateAddedPickupDropoffDisplay()
        self.onPreviewWorldClicked()

class MockSimulationControl:
    def __init__(self):
        # Since this mock class is for running without UI, we don't actually wait for any events.
        self.next_step_event = threading.Event()
        self.masterskip = True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = SimulationControl()
    mainWin.show()
    sys.exit(app.exec_())
