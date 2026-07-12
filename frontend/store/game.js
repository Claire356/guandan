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
const rankLevel = { 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, J: 11, Q: 12, K: 13, A: 14, 小王: 16, 大王: 17 }
const cardRank = card => String(card).includes('大王') ? '大王' : (String(card).includes('小王') ? '小王' : String(card).slice(1))
const suitLevel = { '♦': 1, '♣': 2, '♥': 3, '♠': 4, '🃏': 0 }
const cardSuit = card => typeof card === 'string' ? card.slice(0, 1) : (card.suit === 'Joker' ? '🃏' : card.suit)
const normalizedRank = card => typeof card === 'string' ? cardRank(card) : card.rank
const sortCards = cards => [...cards].sort((first, second) => (
  (rankLevel[normalizedRank(first)] || first.value || 0) - (rankLevel[normalizedRank(second)] || second.value || 0)
  || (suitLevel[cardSuit(first)] ?? 9) - (suitLevel[cardSuit(second)] ?? 9)
))
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))
const aiNamePool = ['牌圣','炸到底','别管我','稳住哥','天选人','王炸王','冲冲冲','赌一手','别炸我','过过过','小钢板','同花顺','起飞啦','逆风局','听我炸']
const shuffle = values => [...values].sort(() => Math.random() - 0.5)
// 离线演示也通过独立身份资料生成，不把昵称和头像写入出牌规则。
const buildOfflineIdentities = () => {
  const avatarIds = shuffle(Array.from({ length: 70 }, (_, index) => index + 1)).slice(0, 3)
  const avatarStyles = shuffle(['高颜值美女','高颜值帅哥','潮流电竞风','都市时尚风','国风写真','二次元真人写真风'])
  return shuffle(aiNamePool).slice(0, 3).map((name, index) => ({
    name,
    avatar: `https://i.pravatar.cc/500?img=${avatarIds[index]}`,
    avatar_style: avatarStyles[index],
    is_human: false,
    team_id: (index + 1) % 2,
    hand_count: 27
  }))
}

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
const identifyOfflineType = (cards, currentLevel = '2') => {
  const length = cards.length
  const groups = groupCards(cards)
  const entries = Object.entries(groups)
  const counts = entries.map(([, items]) => items.length).sort((a, b) => b - a)
  const strength = rank => rank === currentLevel ? 15 : (rankLevel[rank] || 0)
  const levels = entries.map(([rank]) => strength(rank)).sort((a, b) => a - b)
  const wild = cards.filter(card => card === `♥${currentLevel}`)
  if (length === 1 && wild.length) return { type:'invalid', level:0, length }
  // 离线 H5 的逢人配至少覆盖单组牌型；复杂组合无法确定时拒绝，避免放行非法牌。
  if (wild.length && wild.length < length) {
    const normalRanks = cards.filter(card => card !== `♥${currentLevel}`).map(cardRank)
    const ordinary = normalRanks.filter(rank => !['小王','大王'].includes(rank))
    if (ordinary.length && new Set(ordinary).size === 1 && length <= 4) {
      const type = {2:'pair',3:'triple',4:'bomb'}[length]
      return { type, level:strength(ordinary[0]), length, pure:false, suit_level:4 }
    }
  }
  if (length === 4 && cards.filter(card => cardRank(card) === '大王').length === 2 && cards.filter(card => cardRank(card) === '小王').length === 2) return {type:'joker_bomb',level:17,length}
  if (length === 1) return { type: 'single', level: levels[0], length, suit_level:suitLevel[cardSuit(cards[0])] || 0 }
  if (entries.length === 1 && length === 2 && !['小王','大王'].includes(entries[0][0])) return { type: 'pair', level: levels[0], length, suit_level:Math.max(...cards.map(card => suitLevel[cardSuit(card)] || 0)) }
  if (entries.length === 1 && length === 3 && !['小王','大王'].includes(entries[0][0])) return { type: 'triple', level: levels[0], length }
  if (entries.length === 1 && length === 4 && !['小王','大王'].includes(entries[0][0])) return { type: 'bomb', level: levels[0], length, pure:true }
  if (length === 5 && counts.join(',') === '3,2') {
    const triple = entries.find(([, items]) => items.length === 3)
    return { type: 'triple_with_pair', level: rankLevel[triple[0]], length }
  }
  const sequenceLevels = entries.map(([rank]) => rankLevel[rank] || 0).sort((a,b) => a-b)
  if (length >= 5 && entries.length === length && !entries.some(([rank]) => ['2','小王','大王'].includes(rank)) && consecutive(sequenceLevels)) {
    const sameSuit = length === 5 && new Set(cards.map(cardSuit)).size === 1
    return { type:sameSuit ? 'straight_flush' : 'straight', level:sequenceLevels.at(-1), length, suit_level:sameSuit ? suitLevel[cardSuit(cards[0])] : 0 }
  }
  if (length >= 6 && length % 2 === 0 && counts.every(count => count === 2) && !entries.some(([rank]) => rank === '2') && consecutive(sequenceLevels)) return { type: 'double_sequence', level: sequenceLevels.at(-1), length }
  if (length >= 6 && length % 3 === 0 && counts.every(count => count === 3) && !entries.some(([rank]) => rank === '2') && consecutive(sequenceLevels)) return { type: 'steel_plate', level: sequenceLevels.at(-1), length }
  return { type: 'invalid', level: 0, length }
}

const compareOffline = (mine, table) => {
  const bombs = ['straight_flush','bomb','joker_bomb']
  const mineBomb = bombs.includes(mine.type), tableBomb = bombs.includes(table.type)
  if (mineBomb !== tableBomb) return mineBomb ? 1 : -1
  if (mineBomb) {
    const category = {straight_flush:1,bomb:2,joker_bomb:3}
    if (category[mine.type] !== category[table.type]) return category[mine.type] > category[table.type] ? 1 : -1
  } else if (mine.type !== table.type || mine.length !== table.length) return 0
  if (mine.level !== table.level) return mine.level > table.level ? 1 : -1
  if (mine.type === 'bomb' && Boolean(mine.pure) !== Boolean(table.pure)) return mine.pure ? 1 : -1
  if (['pair','straight_flush'].includes(mine.type) && mine.suit_level !== table.suit_level) return mine.suit_level > table.suit_level ? 1 : -1
  return 0
}

const findOfflineResponse = (hand, tableCards, currentLevel = '2') => {
  const tableType = identifyOfflineType(tableCards, currentLevel)
  const groups = groupCards(hand)
  const strength = rank => rank === currentLevel ? 15 : (rankLevel[rank] || 0)
  const entries = Object.entries(groups).sort((a, b) => strength(a[0]) - strength(b[0]))
  const higherGroup = count => entries.find(([rank, cards]) => cards.length >= count && strength(rank) > tableType.level)
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
    const rankCount = tableType.type === 'straight' ? 1 : (tableType.type === 'double_sequence' ? 2 : 3)
    const sequenceSize = tableType.type === 'straight' ? 5 : (tableType.type === 'double_sequence' ? 3 : 2)
    for (let start = 3; start + sequenceSize - 1 <= 14 && !response.length; start += 1) {
      const sequence = Array.from({ length: sequenceSize }, (_, index) => start + index)
      if (sequence[sequence.length - 1] <= tableType.level) continue
      const selected = sequence.map(level => entries.find(([rank, cards]) => rankLevel[rank] === level && cards.length >= rankCount))
      if (selected.every(Boolean)) response = selected.flatMap(([, cards]) => cards.slice(0, rankCount)).slice(0, width * sequenceSize)
    }
  } else if (tableType.type === 'bomb') {
    const bomb = entries.find(([rank, cards]) => cards.length >= 4 && strength(rank) > tableType.level)
    if (bomb) {
      response = bomb[1].slice(0, 4)
    }
  }

  // 普通牌无法压制时，允许 AI 使用最小四张以上炸弹抢回主动权。
  if (!response.length && tableType.type !== 'invalid' && tableType.type !== 'bomb') {
    const bomb = entries.filter(([, cards]) => cards.length >= 4).sort((a, b) => rankLevel[a[0]] - rankLevel[b[0]])[0]
    if (bomb) response = bomb[1].slice(0, 4)
  }
  const responseType = identifyOfflineType(response, currentLevel)
  return response.length && responseType.type !== 'invalid' && compareOffline(responseType, tableType) > 0 ? response : []
}

export const useGameStore = defineStore('game', {
  state: () => ({
    game: null,
    selectedIndices: [],
    hand: demoCards,
    recommendation: [],
    recommendationIndices: [],
    recommendationType: null,
    recommendationReason: '',
    recommendationExpectedValue: 0,
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
      const offlineIdentities = buildOfflineIdentities()
      this.loading = true
      this.strategy = strategy
      this.selectedIndices = []
      this.recommendation = []
      this.recommendationIndices = []
      this.recommendationReason = ''
      this.recommendationExpectedValue = 0
      this.hand = sortCards(newOfflineDeal[0])
      this.offlineAiHands = {}
      this.aiThinking = false
      try {
        const response = await gameApi.startGame(['你', 'AI-1', 'AI-2', 'AI-3'])
        this.game = response.game
        this.hand = sortCards(response.game.current_hand || [])
        this.offlineDemo = false
      } catch (error) {
        this.offlineDemo = true
        this.offlineAiHands = {
          [offlineIdentities[0].name]: sortCards(newOfflineDeal[1]),
          [offlineIdentities[1].name]: sortCards(newOfflineDeal[2]),
          [offlineIdentities[2].name]: sortCards(newOfflineDeal[3])
        }
        this.game = {
          phase: 'ready', round_number: 1,
          players: [{ name: '你', hand_count: 27, team_id: 0, is_human: true, avatar: '' }, ...offlineIdentities],
          state: {
            current_player_index: 0,
            current_level: '2',
            current_turn_count: 0,
            last_played_cards: [],
            last_player_name: null,
            last_action_text: '本轮由你开始',
            table_plays: [],
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
        this.hand = sortCards(response.game.current_hand || [])
      } else {
        // 离线演示同样要保存本次牌面，否则手牌虽被移除，桌面仍会一直显示“等待首出”。
        const playedCards = this.selectedCards
        const currentLevel = this.game.state.current_level || '2'
        const playedType = identifyOfflineType(playedCards, currentLevel)
        if (playedType.type === 'invalid') throw new Error('所选牌不构成合法掼蛋牌型')
        const tableCards = this.game.state.last_played_cards || []
        if (tableCards.length && compareOffline(playedType, identifyOfflineType(tableCards, currentLevel)) <= 0) throw new Error('所选牌无法压过当前桌面牌型')
        const used = new Set(this.selectedIndices)
        this.hand = this.hand.filter((_, index) => !used.has(index))
        this.game.state.last_played_cards = playedCards
        this.game.state.last_player_name = '你'
        this.game.state.last_action_text = `你出了 ${playedCards.join(' ')}`
        this.game.state.table_plays.push({ player: '你', cards: playedCards, is_pass: false })
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
          const name = this.game.players[playerIndex]?.name || `AI-${playerIndex}`
          this.game.state.current_player_index = playerIndex
          this.game.state.last_action_text = `${name} 正在思考…`
          await wait(650)

          const tableCards = this.game.state.last_played_cards || []
          const aiHand = this.offlineAiHands[name] || []
          const responseCards = findOfflineResponse(aiHand, tableCards, this.game.state.current_level || '2')

          if (responseCards.length) {
            responseCards.forEach(card => aiHand.splice(aiHand.indexOf(card), 1))
            this.game.state.last_played_cards = responseCards
            this.game.state.last_player_name = name
            this.game.state.last_action_text = `${name} 出了 ${responseCards.join(' ')}`
            this.game.state.table_plays.push({ player: name, cards: [...responseCards], is_pass: false })
            const player = this.game.players.find(item => item.name === name)
            if (player) player.hand_count = aiHand.length
            this.game.state.log.push(`${name} 出了 ${responseCards.join(' ')}`)
          } else {
            this.game.state.last_action_text = `${name} · PASS`
            this.game.state.table_plays.push({ player: name, cards: [], is_pass: true })
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
        this.hand = sortCards(response.game.current_hand || [])
      } else if ((this.game.state.last_played_cards || []).length) {
        this.game.state.last_action_text = '你 · PASS'
        this.game.state.table_plays.push({ player: '你', cards: [], is_pass: true })
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
        this.recommendationReason = response.reason || '根据当前牌型与手牌结构选择合法收益最高的方案'
        this.recommendationExpectedValue = response.expected_value || 0
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
        const tableCards = this.game.state.last_played_cards || []
        const cards = tableCards.length ? findOfflineResponse(this.hand, tableCards, this.game.state.current_level || '2') : this.hand.filter(card => card !== `♥${this.game.state.current_level || '2'}`).slice(0,1)
        this.recommendation = cards.map(label => ({ label }))
        this.recommendationIndices = cards.map(card => this.hand.indexOf(card)).filter(index => index >= 0)
        this.recommendationType = cards.length ? identifyOfflineType(cards, this.game.state.current_level) : {type:'pass',level:0,length:0}
        this.recommendationReason = cards.length ? '推荐牌已通过当前桌面牌型比较' : '当前没有能够合法压过桌面的牌，建议PASS'
        this.recommendationExpectedValue = 0.56
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
        player: { name: '你', avatar: '' }, overall_score: 68,
        scores: { aggression:68, cooperation:76, emotion:42, risk:55, decision:72 },
        tags: ['侵略型','合作型','冷静型','赌狗型','果断型'],
        dimensions: [
          {key:'aggression',score:68,tag:'侵略型',explanation:'你喜欢主动掌控牌局，乐于争夺牌权。'},
          {key:'cooperation',score:76,tag:'合作型',explanation:'你愿意为了队友牺牲自己的牌型。'},
          {key:'emotion',score:42,tag:'冷静型',explanation:'你的决策较稳定，不容易受到情绪影响。'},
          {key:'risk',score:55,tag:'赌狗型',explanation:'你更愿意冒险，追求高收益打法。'},
          {key:'decision',score:72,tag:'果断型',explanation:'你决策迅速，执行力较强。'}
        ],
        personality_key:'侵-合-冷-赌-果',
        personality_title:{
          title:'冷血赌圣', emoji:'🧊🎰',
          psychology:'面无表情，内心毫无波澜。炸你就炸你，还需要挑日子吗？喂队友就像投喂流浪猫——精准、冷静、不带感情。',
          playstyle:'出牌迅速，炸弹使用果断；喂牌精准，同时保持稳定节奏和情绪。',
          catchphrase:'"炸。接。过。"',
          tags:['人形空调','扑克脸专业八级','队友不敢搭话'],
          warning:'请勿在冬天与该玩家组队，气场过于寒冷。建议携带暖宝宝。'
        },
        summary:'本局决策节奏清晰，兼顾主动争权与队友协作。'
      }
    },
    async loadPersonalityReport() {
      if (this.offlineDemo) return this.report
      try {
        const response = await gameApi.getPersonalityReport()
        this.report = response.report
      } catch (error) {
        if (!this.report) this.finishDemo()
      }
      return this.report
    }
  }
})
