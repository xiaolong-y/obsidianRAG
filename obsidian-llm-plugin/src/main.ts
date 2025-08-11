import { Plugin, PluginSettingTab, Setting } from 'obsidian';

interface ObsidianLLMSettings {
  apiEndpoint: string;
  defaultModel: string;
}

const DEFAULT_SETTINGS: ObsidianLLMSettings = {
  apiEndpoint: 'http://localhost:8000',
  defaultModel: 'gpt-3.5-turbo',
};

export default class ObsidianLLMPlugin extends Plugin {
  settings: ObsidianLLMSettings;

  async onload() {
    console.log('Loading Obsidian LLM Plugin');
    await this.loadSettings();
    // Register commands
    this.addCommand({
      id: 'process-inbox',
      name: 'Process Inbox',
      callback: () => this.processInbox(),
    });
    this.addCommand({
      id: 'generate-synthesis',
      name: 'Generate Synthesis',
      callback: () => this.generateSynthesis(),
    });
    this.addCommand({
      id: 'create-visual-map',
      name: 'Create Visual Map',
      callback: () => this.createVisualMap(),
    });
    this.addCommand({
      id: 'batch-process',
      name: 'Batch Process',
      callback: () => this.batchProcess(),
    });
    // Settings tab
    this.addSettingTab(new LLMPluginSettingTab(this.app, this));
  }

  async onunload() {
    console.log('Unloading Obsidian LLM Plugin');
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  // Command handlers
  async processInbox() {
    console.log('Processing inbox (placeholder)');
  }
  async generateSynthesis() {
    console.log('Generating synthesis (placeholder)');
  }
  async createVisualMap() {
    console.log('Creating visual map (placeholder)');
  }
  async batchProcess() {
    console.log('Batch processing (placeholder)');
  }
}

class LLMPluginSettingTab extends PluginSettingTab {
  plugin: ObsidianLLMPlugin;
  constructor(app: any, plugin: ObsidianLLMPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl('h2', { text: 'LLM Plugin Settings' });
    new Setting(containerEl)
      .setName('API Endpoint')
      .setDesc('URL of the backend API')
      .addText(text =>
        text
          .setPlaceholder('http://localhost:8000')
          .setValue(this.plugin.settings.apiEndpoint)
          .onChange(async value => {
            this.plugin.settings.apiEndpoint = value;
            await this.plugin.saveSettings();
          }),
      );
    new Setting(containerEl)
      .setName('Default Model')
      .setDesc('Model to use for non‑specific queries')
      .addText(text =>
        text
          .setPlaceholder('gpt-3.5-turbo')
          .setValue(this.plugin.settings.defaultModel)
          .onChange(async value => {
            this.plugin.settings.defaultModel = value;
            await this.plugin.saveSettings();
          }),
      );
  }
}