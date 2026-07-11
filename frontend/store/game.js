import { defineStore } from 'pinia'
import * as gameApi from '@/services/game'

const demoCards = ['♠3', '♥3', '♣4', '♦5', '♠6', '♥7', '♣8', '♦9', '♠10', '♥J', '♣Q', '♦K', '♠A', '♥2']
const rankLevel = { 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, J: 11, Q: 12, K: 13, A: 14, 2: 15 }
const cardRank = card => String(card).slice(1)
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

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
    offlineAiHands: {},
    aiThinking: false,
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
      this.offlineAiHands = {}
      this.aiThinking = false
      try {
        const response = await gameApi.startGame(['你', 'AI-1', 'AI-2', 'AI-3'])
        this.game = response.game
        this.hand = response.game.current_hand || []
        this.offlineDemo = false
      } catch (error) {
        this.offlineDemo = true
        this.offlineAiHands = {
          'AI-1': [...demoCards.slice(2), ...demoCards.slice(0, 2)],
          'AI-2': [...demoCards.slice(4), ...demoCards.slice(0, 4)],
          'AI-3': [...demoCards.slice(6), ...demoCards.slice(0, 6)]
        }
        this.game = {
          phase: 'ready', round_number: 1,
          players: ['你', 'AI-1', 'AI-2', 'AI-3'].map((name, index) => ({ name, hand_count: demoCards.length, team_id: index < 2 ? 0 : 1 })),
          state: {
            current_player_index: 0,
            current_turn_count: 0,
            last_played_cards: [],
            last_player_name: null,
            last_action_text: '本轮由你开始',
            log: ['离线演示已开始']
          }
        }
      } finally {
        this.loading = false
      }
    },
    toggleCard(index) {
      if (this.aiThinking) return
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
        // 离线演示同样要保存本次牌面，否则手牌虽被移除，桌面仍会一直显示“等待首出”。
        const playedCards = this.selectedCards
        const used = new Set(this.selectedIndices)
        this.hand = this.hand.filter((_, index) => !used.has(index))
        this.game.state.last_played_cards = playedCards
        this.game.state.last_player_name = '你'
        this.game.state.last_action_text = `你出了 ${playedCards.join(' ')}`
        this.game.state.current_turn_count += 1
        this.game.state.log.push(`你出了 ${playedCards.join(' ')}`)
        const human = this.game.players.find(player => player.name === '你')
        if (human) human.hand_count = this.hand.length
        this.selectedIndices = []
        await this.runOfflineAiTurns()
        return true
      }
      this.selectedIndices = []
      return true
    },
    async runOfflineAiTurns() {
      this.aiThinking = true
      try {
        for (let playerIndex = 1; playerIndex <= 3; playerIndex += 1) {
          const name = `AI-${playerIndex}`
          this.game.state.current_player_index = playerIndex
          this.game.state.last_action_text = `${name} 正在思考…`
          await wait(650)

          const tableCards = this.game.state.last_played_cards || []
          const aiHand = this.offlineAiHands[name] || []
          let playIndex = -1

          // 离线规则演示只在桌面为单张时寻找刚好能压过的最小牌；其他牌型选择 PASS。
          if (tableCards.length === 1) {
            const tableLevel = rankLevel[cardRank(tableCards[0])] || 0
            let bestLevel = Number.POSITIVE_INFINITY
            aiHand.forEach((card, index) => {
              const level = rankLevel[cardRank(card)] || 0
              if (level > tableLevel && level < bestLevel) {
                bestLevel = level
                playIndex = index
              }
            })
          }

          if (playIndex >= 0) {
            const [card] = aiHand.splice(playIndex, 1)
            this.game.state.last_played_cards = [card]
            this.game.state.last_player_name = name
            this.game.state.last_action_text = `${name} 出了 ${card}`
            const player = this.game.players.find(item => item.name === name)
            if (player) player.hand_count = aiHand.length
            this.game.state.log.push(`${name} 出了 ${card}`)
          } else {
            this.game.state.last_action_text = `${name} · PASS`
            this.game.state.log.push(`${name} 选择 PASS`)
          }
          this.game.state.current_turn_count += 1
          await wait(650)
        }
      } finally {
        this.game.state.current_player_index = 0
        this.aiThinking = false
      }
    },
    async pass() {
      if (this.aiThinking) throw new Error('请等待 AI 完成出牌')
      if (!this.offlineDemo) {
        const response = await gameApi.passTurn()
        this.game = response.game
        this.hand = response.game.current_hand || []
      } else if ((this.game.state.last_played_cards || []).length) {
        this.game.state.last_action_text = '你 · PASS'
        this.game.state.log.push('你选择 PASS')
        this.game.state.current_turn_count += 1
        await this.runOfflineAiTurns()
      } else {
        throw new Error('当前拥有主动出牌权，不能 PASS')
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
