import { defineStore } from 'pinia'
import * as gameApi from '@/services/game'

// 离线模式同样严格使用两副牌：2 × 54 = 108 张，轮流发给四家，每家 27 张且无底牌。
const buildOfflineDeal = () => {
  const suits = ['♠', '♥', '♣', '♦']
  const ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
  const deck = []
  for (let copy = 0; copy < 2; copy += 1) {
    suits.forEach(suit => ranks.forEach(rank => deck.push(`${suit}${rank}`)))
    deck.push('🃏小王', '🃏大王')
  }
  // Fisher-Yates 洗牌，避免固定发牌导致各家牌型分布失真。
  for (let index = deck.length - 1; index > 0; index -= 1) {
    const target = Math.floor(Math.random() * (index + 1))
    ;[deck[index], deck[target]] = [deck[target], deck[index]]
  }
  const hands = [[], [], [], []]
  deck.forEach((card, index) => hands[index % 4].push(card))
  return hands
}
const offlineDeal = buildOfflineDeal()
const demoCards = offlineDeal[0]
const rankLevel = { 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, J: 11, Q: 12, K: 13, A: 14, 2: 15, 小王: 16, 大王: 17 }
const cardRank = card => String(card).slice(1)
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

const groupCards = cards => {
  const groups = {}
  cards.forEach(card => {
    const rank = cardRank(card)
    if (!groups[rank]) groups[rank] = []
    groups[rank].push(card)
  })
  return groups
}

const consecutive = levels => levels.every((level, index) => index === 0 || level === levels[index - 1] + 1)

// 识别离线对打所需的核心牌型；返回结构与后端 card_type 保持一致。
const identifyOfflineType = cards => {
  const length = cards.length
  const groups = groupCards(cards)
  const entries = Object.entries(groups)
  const counts = entries.map(([, items]) => items.length).sort((a, b) => b - a)
  const levels = entries.map(([rank]) => rankLevel[rank] || 0).sort((a, b) => a - b)
  if (length === 1) return { type: 'single', level: levels[0], length }
  if (entries.length === 1 && length === 2) return { type: 'pair', level: levels[0], length }
  if (entries.length === 1 && length === 3) return { type: 'triple', level: levels[0], length }
  if (entries.length === 1 && length >= 4) return { type: 'bomb', level: levels[0], length }
  if (length === 5 && counts.join(',') === '3,2') {
    const triple = entries.find(([, items]) => items.length === 3)
    return { type: 'triple_with_pair', level: rankLevel[triple[0]], length }
  }
  if (length === 5 && entries.length === 5 && !levels.includes(15) && consecutive(levels)) return { type: 'straight', level: levels[4], length }
  if (length === 6 && counts.join(',') === '2,2,2' && consecutive(levels)) return { type: 'double_sequence', level: levels[2], length }
  if (length === 6 && counts.join(',') === '3,3' && consecutive(levels)) return { type: 'steel_plate', level: levels[1], length }
  return { type: 'invalid', level: 0, length }
}

const findOfflineResponse = (hand, tableCards) => {
  const tableType = identifyOfflineType(tableCards)
  const groups = groupCards(hand)
  const entries = Object.entries(groups).sort((a, b) => (rankLevel[a[0]] || 0) - (rankLevel[b[0]] || 0))
  const higherGroup = count => entries.find(([rank, cards]) => cards.length >= count && (rankLevel[rank] || 0) > tableType.level)
  let response = []

  if (tableType.type === 'single') {
    const group = higherGroup(1)
    if (group) response = group[1].slice(0, 1)
  } else if (tableType.type === 'pair') {
    const group = higherGroup(2)
    if (group) response = group[1].slice(0, 2)
  } else if (tableType.type === 'triple') {
    const group = higherGroup(3)
    if (group) response = group[1].slice(0, 3)
  } else if (tableType.type === 'triple_with_pair') {
    const triple = higherGroup(3)
    const pair = entries.find(([rank, cards]) => cards.length >= 2 && (!triple || rank !== triple[0]))
    if (triple && pair) response = [...triple[1].slice(0, 3), ...pair[1].slice(0, 2)]
  } else if (['straight', 'double_sequence', 'steel_plate'].includes(tableType.type)) {
    const width = tableType.type === 'straight' ? 5 : (tableType.type === 'double_sequence' ? 2 : 3)
    const rankCount = tableType.type === 'straight' ? 1 : 3
    const sequenceSize = tableType.type === 'straight' ? 5 : (tableType.type === 'double_sequence' ? 3 : 2)
    for (let start = 3; start + sequenceSize - 1 <= 14 && !response.length; start += 1) {
      const sequence = Array.from({ length: sequenceSize }, (_, index) => start + index)
      if (sequence[sequence.length - 1] <= tableType.level) continue
      const selected = sequence.map(level => entries.find(([rank, cards]) => rankLevel[rank] === level && cards.length >= rankCount))
      if (selected.every(Boolean)) response = selected.flatMap(([, cards]) => cards.slice(0, rankCount)).slice(0, width * sequenceSize)
    }
  } else if (tableType.type === 'bomb') {
    const bomb = entries.find(([rank, cards]) => cards.length > tableType.length || (cards.length === tableType.length && rankLevel[rank] > tableType.level))
    if (bomb) {
      const responseLength = bomb[1].length > tableType.length ? tableType.length + 1 : tableType.length
      response = bomb[1].slice(0, responseLength)
    }
  }

  // 普通牌无法压制时，允许 AI 使用最小四张以上炸弹抢回主动权。
  if (!response.length && tableType.type !== 'invalid' && tableType.type !== 'bomb') {
    const bomb = entries.filter(([, cards]) => cards.length >= 4).sort((a, b) => a[1].length - b[1].length || rankLevel[a[0]] - rankLevel[b[0]])[0]
    if (bomb) response = bomb[1].slice(0, 4)
  }
  return response
}

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
      const newOfflineDeal = buildOfflineDeal()
      this.loading = true
      this.strategy = strategy
      this.selectedIndices = []
      this.recommendation = []
      this.recommendationIndices = []
      this.hand = [...newOfflineDeal[0]]
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
          'AI-1': [...newOfflineDeal[1]],
          'AI-2': [...newOfflineDeal[2]],
          'AI-3': [...newOfflineDeal[3]]
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
        const playedType = identifyOfflineType(playedCards)
        if (playedType.type === 'invalid') throw new Error('所选牌不构成合法掼蛋牌型')
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
          const responseCards = findOfflineResponse(aiHand, tableCards)

          if (responseCards.length) {
            responseCards.forEach(card => aiHand.splice(aiHand.indexOf(card), 1))
            this.game.state.last_played_cards = responseCards
            this.game.state.last_player_name = name
            this.game.state.last_action_text = `${name} 出了 ${responseCards.join(' ')}`
            const player = this.game.players.find(item => item.name === name)
            if (player) player.hand_count = aiHand.length
            this.game.state.log.push(`${name} 出了 ${responseCards.join(' ')}`)
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
