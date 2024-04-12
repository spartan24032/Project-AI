import sys

import xlsxwriter
import pandas as pd
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal

import threading
from environment import GridWorld
from agent import Agent
from policies import PRandom, PExploit, PGreedy
from runSimulation import SimulationWorker
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

"""
qThreading and the agent/worker relationship idea is sourced from
https://realpython.com/python-pyqt-qthread/
"""

class SimulationControl(QMainWindow):
    #self.agents, env, episode, step, self.r
    update_display_signal = pyqtSignal(object, object, int, int, int, bool)


    def __init__(self):
        super().__init__()
        self.addedAgents = []
        self.pickupCoords = []
        self.dropoffCoords = []
        self.agentLabels = []
        self.initUI()
        self.masterskip = False
        self.created = False

    def initUI(self):
        self.setWindowTitle('Simulation Control')
        self.setGeometry(100, 100, 1200, 1200)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: World Creation
        self.worldCreationTab = QWidget()
        self.scrollArea = QScrollArea()
        self.tabs.addTab(self.scrollArea, "World Creation")
        self.initWorldCreationTab()
        # Tab 2: Simulation Control
        self.simulationControlTab = QWidget()
        self.tabs.addTab(self.simulationControlTab, "Simulation")
        self.initSimulationControlTab()
        # Tab 3: Charts and Data
        self.qTableTab = QWidget()
        self.tabs.addTab(self.qTableTab, "Charts and Data")

        self.tabs.currentChanged.connect(self.onTabChange)

    def onTabChange(self, index):
        if self.created:
            self.onPauseClicked()
            if self.tabs.widget(index) == self.qTableTab:
                self.populateComboboxes(self.tabagents)

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
        # override policy selection
        self.overridePolicyComboBox = QComboBox(self)
        self.overridePolicyComboBox.addItem("None")
        self.overridePolicyComboBox.addItem("PRandom")
        self.overridePolicyComboBox.addItem("PExploit")
        self.overridePolicyComboBox.addItem("PGreedy")
        self.overrideTerminationStepInput = QLineEdit(self)
        self.overrideTerminationStepInput.setPlaceholderText("None")
        overridePolicyLayout = QHBoxLayout()
        overridePolicyLayout.addWidget(QLabel("Override Policy:"))
        overridePolicyLayout.addWidget(self.overridePolicyComboBox)
        overridePolicyLayout.addWidget(QLabel(" until step/episode: "))
        overridePolicyLayout.addWidget(self.overrideTerminationStepInput)
        self.overrideTerminationStepInput.setMaximumWidth(100)
        overridePolicyLayout.addWidget(QLabel(" (will return to default after this)"))
        overridePolicyLayout.addStretch()
        layout.addLayout(overridePolicyLayout)
        self.overrideDisclaimer = QLabel(
            "This will go to a step # in step-based simulation and an episode # in episode-based simulation"
        )
        self.overrideDisclaimer.setStyleSheet("color: #4a4a4a; font: italic;")
        layout.addWidget(self.overrideDisclaimer)

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
        #self.worldCreationTab.setLayout(layout)
        worldCreationContent = QWidget()
        worldCreationContent.setLayout(layout)

        self.scrollArea.setWidgetResizable(True)  # Allows the scroll area to adapt to the size of its content
        self.scrollArea.setWidget(worldCreationContent)
######
    def initSimulationControlTab(self):

        layout = QGridLayout()
        layout.setRowStretch(5, 1)
        self.episodeLabel = QLabel("Episode: 0")
        layout.addWidget(self.episodeLabel, 0, 0, 1, -1)
        self.episodeLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        layout.setRowMinimumHeight(0, 1)

        # Simulation display area for images or text
        self.worldStateContainer = QFrame(self)
        self.worldStateContainer.setFrameShape(QFrame.StyledPanel)
        self.worldStateGrid = QGridLayout()
        self.worldStateContainer.setLayout(self.worldStateGrid)

        layout.addWidget(self.worldStateContainer, 1, 0, 1, -1)
        self.simulationControlTab.setLayout(layout)
        self.initWorldStateGrid(5)

        self.spacerFrame = QFrame(self)
        self.spacerFrame.setFixedSize(100, 100)
        layout.addWidget(self.spacerFrame, 0, 5, 1, 1)

        self.qValuesScrollArea = QScrollArea(self.simulationControlTab)
        self.qValuesScrollArea.setWidgetResizable(True)
        self.qValuesScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.qValuesContainer = QWidget()
        self.qValuesScrollArea.setWidget(self.qValuesContainer)
        self.qValuesLayout = QVBoxLayout(self.qValuesContainer)

        placeholderLabel = QLabel(
            "Current Agent State and Q-Values")
        placeholderLabel.setStyleSheet("margin: 10px;")
        self.qValuesLayout.addWidget(placeholderLabel)

        self.qValuesScrollArea.setWidget(self.qValuesContainer)
        layout.addWidget(self.qValuesScrollArea, 0, 6, 5, -1)
        self.qValuesLayout.addStretch()

        # Button to proceed to the next step
        self.nextBtn = QPushButton('Next', self)
        self.nextBtn.clicked.connect(self.onNextClicked)
        layout.addWidget(self.nextBtn, 2, 0)

        # Button to play continuously
        self.playBtn = QPushButton('Play', self)
        self.playBtn.clicked.connect(self.onPlayClicked)
        layout.addWidget(self.playBtn, 2, 1)

        # Button to pause autoplay
        self.pauseBtn = QPushButton('Pause', self)
        self.pauseBtn.clicked.connect(self.onPauseClicked)
        layout.addWidget(self.pauseBtn, 2, 2)

        # Input for skipping steps
        self.skipInput = QLineEdit(self)
        self.skipInput.setPlaceholderText('steps/episodes to skip')
        self.skipInput.setMaximumWidth(250)
        layout.addWidget(self.skipInput, 4, 0)

        # Button to skip steps
        self.skipBtn = QPushButton('Skip there', self)
        self.skipBtn.clicked.connect(self.onSkipClicked)
        self.skipBtn.setMaximumWidth(150)
        layout.addWidget(self.skipBtn, 4, 1)

        # Slider for controlling autoplay speed
        self.speedSlider = QSlider(Qt.Horizontal)
        self.speedSlider.setMinimum(1)
        self.speedSlider.setMaximum(20)
        self.speedSlider.setValue(15)  # Default value

        # Label to display slider value
        self.speedValueLabel = QLabel("15")  # Initialize with default slider value
        self.speedSlider.valueChanged.connect(self.updateSpeedValue)  # Connect signal to slot

        # Layout adjustments to include the slider and its value label
        layout.addWidget(QLabel("Speed:"), 3, 0)
        layout.addWidget(self.speedSlider, 3, 1, 1, 2)
        layout.addWidget(self.speedValueLabel, 3, 3)  # Display the current speed value next to the slider

        self.simulationControlTab.setLayout(layout)
        self.nextBtn.setEnabled(False)
        self.playBtn.setEnabled(False)
        self.pauseBtn.setEnabled(False)
        self.skipInput.setEnabled(False)
        self.skipBtn.setEnabled(False)
        self.speedSlider.setEnabled(False)
######
    def initChartsDataTab(self):
        mainLayout = QVBoxLayout(self.qTableTab)
        self.nestedTabs = QTabWidget()
        mainLayout.addWidget(self.nestedTabs)

        self.qTablesDisplayTab = QWidget()
        self.nestedTabs.addTab(self.qTablesDisplayTab, "Q-Tables")

        self.graphsTab = QWidget()
        self.nestedTabs.addTab(self.graphsTab, "Graphs")
        self.builtQtable = False
        self.setupQTablesDisplayTab()

######################################################################
    def initWorldStateGrid(self, size, agents=[], pickups=[], dropoffs=[]):
        self.clearLayout(self.worldStateGrid)

        for row in range(size):
            for col in range(size):
                cellLabel = QLabel(f"{row},{col}")
                cellLabel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
                cellLabel.setAlignment(Qt.AlignCenter)
                cellLabel.setStyleSheet("border: 1px solid black;")
                cellLabel.setFixedSize(int(600/size), int(600/size))

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

        self.worldStateContainer.setFixedSize(700, 700)

    def updateDisplay(self, agents, env, ep, step, r, ep_based, totalsteps):
        self.tabagents = agents
        self.tabenv = env
        if ep_based:
            self.episodeLabel.setText(f"Episode: {ep}/{r}, Step: {step}, Total Steps: {totalsteps}")
        else:
            self.episodeLabel.setText(f"Step: {totalsteps}/{r}, Episode: #{ep} (total runs completed)")
        size, actions, dropoffStorage, pickups, dropoffs, used_dropoffs = env.UIrenderVals()
        for row in range(size):
            for col in range(size):
                cell_label = self.worldStateGrid.itemAtPosition(row, col).widget()
                base_content = ' '
                cell_style = "QLabel { font-weight: bold; border: 1px solid black; "
                cell_style += "background-color: white; color: black; "

                # Check for pickups and dropoffs
                if (row, col) in pickups:
                    base_content = f'P{pickups[(row, col)]}'
                    cell_style += "background-color: #3498db; color: white; "  # Light blue background
                elif (row, col) in dropoffs:
                    base_content = f'D{dropoffs[(row, col)]}'
                    cell_style += "background-color: #2ecc71; color: white; "  # Green background

                # Overlay agents
                for idx, agent in enumerate(agents):
                    agent_state, has_item = agent.get_state()
                    if agent_state == (row, col):
                        agent_mark = 'C' if has_item else 'A'
                        agent_id = str(idx)
                        base_content = f"{agent_mark}{agent_id}"
                        cell_style += "background-color: #e74c3c; color: white; "  # Red background for agent
                        break

                cell_style += "}"

                cell_label.setText(base_content)
                cell_label.setStyleSheet(cell_style)

    # idx, agent_buffer, valid_actions_current, pd_string, action, reward
    def updateQValuesDisplay(self, idx, agents, valid_actions, pd_string, action, reward):
        if 0 <= idx < len(agents):
            agent = agents[idx]  # Access the specific agent
            Q_dicts = agent.return_q_dicts()
            policy = agent.get_policy()
            state, has_item = agent.get_state()

            # Initialize the text for this agent's Q-values display
            q_values_text = (f"Agent {idx} at {state}, has item: {has_item}\n"
                             f"Valid actions: {valid_actions}\n")
            if pd_string != 5:
                q_values_text += f"Complex_space2 P/D string: {pd_string}\n"
            q_values_text += "Q-values:\n"
            for action_key in agent.actions:
                try:
                    q_value = Q_dicts[pd_string].get((state, has_item, action_key), "--")
                except:
                    return
                display_value = f"{q_value:.2f}" if q_value != "--" else "--"
                q_values_text += f"    {action_key}: {display_value}\n"
            q_values_text += f"using policy: {policy}\n"
            q_values_text += f"chooses action: {action}, Reward: {reward}"

            # Update only the QLabel for the agent specified by idx
            self.updateAgentLabel(idx, q_values_text)

        self.qValuesLayout.addStretch()  # Ensures content is top-aligned

    def updateAgentLabel(self, idx, text):
        if idx >= len(self.agentLabels):
            for _ in range(len(self.agentLabels), idx + 1):
                label = QLabel()
                label.setStyleSheet("margin: 5px; padding: 5px; border: 1px solid black; background-color: #fcba03;")
                self.qValuesLayout.addWidget(label)
                self.agentLabels.append(label)
        self.agentLabels[idx].setText(text)

    def onNextClicked(self):
        if self.simulationWorker:
            self.simulationWorker.requestNext.emit()

    def onPlayClicked(self):
        self.playBtn.setEnabled(False)
        self.nextBtn.setEnabled(False)
        self.speedSlider.setEnabled(False)
        self.skipBtn.setEnabled(False)
        self.skipInput.setEnabled(False)
        if self.simulationWorker:
            speed = int(self.speedSlider.value())
            self.simulationWorker.requestPlay.emit(speed)

    def onPauseClicked(self):
        self.playBtn.setEnabled(True)
        self.nextBtn.setEnabled(True)
        self.speedSlider.setEnabled(True)
        self.skipBtn.setEnabled(True)
        self.skipInput.setEnabled(True)
        if self.simulationWorker:
            self.simulationWorker.requestPause.emit()

    def onSkipClicked(self):
        if self.simulationWorker:
            skips = int(self.skipInput.text())
            self.simulationWorker.requestSkip.emit(skips)
            self.simulationWorker.requestNext.emit()

    def updateSpeedValue(self, value):
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
        self.tabs.setCurrentIndex(self.tabs.indexOf(self.simulationControlTab))
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

        override_text = self.overridePolicyComboBox.currentText()
        override_policy = {
            "None": None, "PGreedy": PGreedy, "PExploit": PExploit, "PRandom": PRandom
        }.get(override_text, None)

        termination_step_text = self.overrideTerminationStepInput.text().strip()
        termination_step = 0
        if termination_step_text:
            try:
                termination_step = int(termination_step_text)
            except ValueError:
                print("Invalid input for termination step, defaulting to 0")
                termination_step = 0

        for agentConfig in self.addedAgents:
            start_state = self.parseCoordinateToTuple(agentConfig[0])
            policy = {"PGreedy": PGreedy, "PExploit": PExploit, "PRandom": PRandom}.get(agentConfig[1])
            learning_algorithm = agentConfig[2]
            alpha = float(agentConfig[3]) if agentConfig[3] else 0.7
            gamma = float(agentConfig[4]) if agentConfig[4] else 0.8

            # actions, start_state, policy, learning_algorithm, alpha, gamma, override_policy, override_max_step
            agent = Agent(
                env.actions,
                start_state=start_state,
                policy=policy,
                learning_algorithm=learning_algorithm,
                alpha=alpha,
                gamma=gamma,
                override_policy=override_policy,
                override_max_step=termination_step
            )
            agentInstances.append(agent)

        complex_world2 = self.complexWorldCheck.isChecked()
        episode_based = self.isEpisodeBased
        r = int(self.episodesOrStepsInput.text())
        # Run simulation
        self.initWorldStateGrid(size, agentInstances, pickups, dropoffs)

        # (self, agents, complex_world2, episode_based, r, sim_control)
        # Create the thread and worker
        self.simulationThread = QThread()
        self.simulationWorker = SimulationWorker(agentInstances, env, complex_world2, episode_based, r, False)
        self.simulationWorker.moveToThread(self.simulationThread)

        # Connect signals and slots
        self.simulationThread.started.connect(self.simulationWorker.run_simulation)
        self.simulationWorker.finished.connect(self.simulationThread.quit)
        self.simulationWorker.finished.connect(self.simulationWorker.deleteLater)
        self.simulationThread.finished.connect(self.simulationThread.deleteLater)
        self.simulationWorker.update_display.connect(self.updateDisplay)
        self.simulationWorker.update_qtable_display.connect(self.updateQValuesDisplay)

        # Start the simulation thread
        self.simulationThread.start()
        self.nextBtn.setEnabled(True)
        self.playBtn.setEnabled(True)
        self.pauseBtn.setEnabled(True)
        self.skipInput.setEnabled(True)
        self.skipBtn.setEnabled(True)
        self.speedSlider.setEnabled(True)
        self.created = True
        self.initChartsDataTab()

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
                    # print("Agent at", row, col)
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

#########
    def setupQTablesDisplayTab(self):
        layout = QVBoxLayout()

        self.agentSelectCombo = QComboBox()
        layout.addWidget(self.agentSelectCombo)

        self.pdStringSelectCombo = QComboBox()
        layout.addWidget(self.pdStringSelectCombo)

        self.qTableWidget = QTableWidget()
        self.qTableWidget.setRowCount(0)
        self.qTableWidget.setColumnCount(4)
        self.qTableWidget.setHorizontalHeaderLabels(['State', 'Has Item', 'Action', 'Value'])
        self.qTableWidget.setSortingEnabled(True)
        header = self.qTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        font = header.font()
        font.setBold(True)
        header.setFont(font)

        layout.addWidget(self.qTableWidget)

        self.exportButton = QPushButton("Export to Excel", self)
        self.exportButton.clicked.connect(self.exportToExcel)
        layout.addWidget(self.exportButton)

        self.qTablesDisplayTab.setLayout(layout)
        try:
            self.populateComboboxes(self.tabagents)
        except:
            return

    def force_populate_q_table(self, original_q_table, world_size, actions):
        # Copy the original dictionary to avoid modifying it directly
        full_q_table = dict(original_q_table)

        # Generate all possible combinations
        for x in range(world_size):
            for y in range(world_size):
                for has_item in [False, True]:
                    for action in actions:
                        state = (x, y)
                        key = (state, has_item, action)
                        if key not in full_q_table:
                            full_q_table[key] = 0  # Fill missing entries with 0

        return full_q_table

    def exportToExcel(self):
        agent_index = self.agentSelectCombo.currentIndex()
        pd_string = self.pdStringSelectCombo.currentText()
        if agent_index == -1 or not pd_string:
            print("No agent or PD string selected.")
            return

        selected_agent = self.tabagents[agent_index]
        q_table = selected_agent.return_q_dicts().get(pd_string, {})

        world_size = self.tabenv.get_size()
        actions = self.tabenv.get_actions()  # List of actions like ['N', 'E', 'S', 'W', 'pickup', 'dropoff']
        populated_qtable = self.force_populate_q_table(q_table, world_size, actions)
        # Prompt user to save the file
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx);;All Files (*)",
                                                  options=options)
        if not filename:
            return

        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet(f"Agent_{agent_index}_{pd_string}")

        # Set the headers
        headers = ['Location', 'Has Item'] + actions
        worksheet.write_row('A1', headers)

        # Prepare data rows
        row = 1
        for x in range(world_size):
            for y in range(world_size):
                for has_item in [True, False]:
                    data = [f"({x},{y})", int(has_item)]
                    for action in actions:
                        key = ((x, y), has_item, action)
                        value = populated_qtable.get(key, 0)
                        data.append(round(value, 2))
                    worksheet.write_row(row, 0, data)
                    row += 1

        workbook.close()
        print(f"Data exported successfully to {filename}")

    def initializeQTableWidget(self):
        world_size = self.tabenv.get_size()
        self.builtQtable = True
        actions = self.tabenv.get_actions()
        self.qTableWidget.setRowCount(world_size * world_size * 2 * len(actions))
        row = 0
        for x in range(world_size):
            for y in range(world_size):
                for has_item in [False, True]:
                    for action in actions:
                        state_str = f"({x},{y})"
                        has_item_str = "True" if has_item else "False"
                        self.qTableWidget.setItem(row, 0, QTableWidgetItem(state_str))
                        self.qTableWidget.setItem(row, 1, QTableWidgetItem(has_item_str))
                        self.qTableWidget.setItem(row, 2, QTableWidgetItem(action))
                        self.qTableWidget.setItem(row, 3, QTableWidgetItem("--"))
                        row += 1

        self.qTableWidget.resizeColumnsToContents()

    def populateComboboxes(self, agents):
        if not self.builtQtable:
            self.initializeQTableWidget()
        self.tabagents = agents
        self.agentSelectCombo.clear()
        self.agentSelectCombo.addItems([f"Agent {i}" for i in range(len(self.tabagents))])
        if self.tabagents:
            self.updatePdStringDropdown()

        self.agentSelectCombo.currentIndexChanged.connect(self.updatePdStringDropdown)
        self.pdStringSelectCombo.currentIndexChanged.connect(self.displayQTable)

    def updatePdStringDropdown(self):
        self.pdStringSelectCombo.clear()
        selected_index = self.agentSelectCombo.currentIndex()
        if 0 <= selected_index < len(self.tabagents):
            selected_agent = self.tabagents[selected_index]
            pd_strings = list(selected_agent.return_q_dicts().keys())
            self.pdStringSelectCombo.addItems(pd_strings)
            self.displayQTable()

    def displayQTable(self):
        agent_index = self.agentSelectCombo.currentIndex()
        pd_string = self.pdStringSelectCombo.currentText()
        if 0 <= agent_index < len(self.tabagents) and pd_string:
            selected_agent = self.tabagents[agent_index]
            qtable = selected_agent.return_q_dicts().get(pd_string, {})
            self.qTableWidget.setRowCount(len(qtable))
            for row, ((state, has_item, action), value) in enumerate(qtable.items()):
                state_item = QTableWidgetItem(str(state))
                has_item_item = QTableWidgetItem(str(has_item))
                action_item = QTableWidgetItem(str(action))
                value_item = QTableWidgetItem(f"{value:.3f}")
                value_item.setData(Qt.UserRole, float(value))

                # Set background color if the Q-value is positive
                if value > 0:
                    green_background = QColor('#b6ffa3')  # Solid green
                    state_item.setBackground(green_background)
                    has_item_item.setBackground(green_background)
                    action_item.setBackground(green_background)
                    value_item.setBackground(green_background)

                self.qTableWidget.setItem(row, 0, state_item)
                self.qTableWidget.setItem(row, 1, has_item_item)
                self.qTableWidget.setItem(row, 2, action_item)
                self.qTableWidget.setItem(row, 3, value_item)
        else:
            self.qTableWidget.setRowCount(0)
        self.qTableWidget.resizeColumnsToContents()

        if self.pdStringSelectCombo.count() == 1:
            self.pdStringSelectCombo.setEnabled(False)  # Disable dropdown if only one option
        else:
            self.pdStringSelectCombo.setEnabled(True)

#########
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
