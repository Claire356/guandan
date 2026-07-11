import { defineStore } from 'pinia'
import * as gameApi from '@/api/game'

const demoCards = ['♠3', '♥3', '♣4', '♦5', '♠6', '♥7', '♣8', '♦9', '♠10', '♥J', '♣Q', '♦K', '♠A', '♥2']

export const useGameStore = defineStore('game', {
  state: () => ({
    game: null,
    selectedIndices: [],
    hand: demoCards,
    recommendation: [],
    recommendationIndices: [],
    recommendationType: null,
    history: [],
    logs: [],
    strategy: 'balanced',
    loading: false,
    offlineDemo: false,
    result: null,
    report: null
  }),
  getters: {
    currentPlayer: state => state.game?.players?.[state.game?.state?.current_player_index || 0],
    selectedCards: state => state.selectedIndices.map(index => state.hand[index]).filter(Boolean)
  },
  actions: {
    async beginTraining(strategy = 'balanced') {
      this.loading = true
      this.strategy = strategy
      this.selectedIndices = []
      this.recommendation = []
      this.recommendationIndices = []
      this.hand = [...demoCards]
      try {
        const response = await gameApi.startGame(['你', 'AI-1', 'AI-2', 'AI-3'])
        this.game = response.game
        this.hand = response.game.current_hand || []
        this.offlineDemo = false
      } catch (error) {
        this.offlineDemo = true
        this.game = {
          phase: 'ready', round_number: 1,
          players: ['你', 'AI-1', 'AI-2', 'AI-3'].map((name, index) => ({ name, hand_count: 27, team_id: index < 2 ? 0 : 1 })),
          state: { current_player_index: 0, current_turn_count: 0, log: ['离线演示已开始'] }
        }
      } finally {
        this.loading = false
      }
    },
    toggleCard(index) {
      this.selectedIndices = this.selectedIndices.includes(index)
        ? this.selectedIndices.filter(item => item !== index)
        : [...this.selectedIndices, index]
    },
    async playSelected() {
      if (!this.selectedIndices.length) throw new Error('请先选择要出的牌')
      if (!this.offlineDemo) {
        const response = await gameApi.playCards(this.selectedIndices)
        this.game = response.game
        this.hand = response.game.current_hand || []
      } else {
        const used = new Set(this.selectedIndices)
        this.hand = this.hand.filter((_, index) => !used.has(index))
      }
      this.selectedIndices = []
      return true
    },
    async pass() {
      if (!this.offlineDemo) {
        const response = await gameApi.passTurn()
        this.game = response.game
        this.hand = response.game.current_hand || []
      }
    },
    async recommend() {
      if (!this.offlineDemo) {
        const response = await gameApi.getRecommendation(this.strategy)
        this.recommendation = response.cards
        this.recommendationType = response.card_type
        const used = new Set()
        this.recommendationIndices = response.cards.map(card => {
          const index = this.hand.findIndex((handCard, handIndex) => (
            !used.has(handIndex)
            && handCard.suit === card.suit
            && handCard.rank === card.rank
            && handCard.value === card.value
            && handCard.is_joker === card.is_joker
          ))
          if (index >= 0) used.add(index)
          return index
        }).filter(index => index >= 0)
      } else {
        this.recommendation = this.hand.slice(0, 1).map(label => ({ label }))
        this.recommendationIndices = this.hand.length ? [0] : []
        this.recommendationType = { type: 'single', level: 3, length: 1 }
      }
    },
    async loadHistory() {
      try {
        const response = await gameApi.getHistory()
        this.history = response.turns
        this.logs = response.logs
      } catch (error) {
        this.history = [
          { player: '你', pattern: 'straight', message: '出牌成功', cards: [] },
          { player: 'AI-1', pattern: 'pass', message: '选择过牌', cards: [] }
        ]
        this.logs = ['训练开始', '完成一次顺子决策']
      }
    },
    finishDemo() {
      this.result = { rank: 1, score: 86, title: '头游', bombCount: 2, passCount: 5 }
      this.report = {
        personality: '均衡稳健型',
        summary: '整体牌序清晰，关键轮次保持了较好的资源控制。',
        mistake: '中盘有一次过早拆对，削弱了后续接牌能力。',
        suggestion: '保留中高对子，在队友取得主动权时优先观察一轮。',
        metrics: { attack: 68, cooperation: 76, risk: 55, hesitation: 38, emotion: 82 }
      }
    }
  }
})
