<template>
  <view class="training-page safe-bottom">
    <view class="ambient"></view><text class="watermark">♠　♥　♦　♣</text>
    <main class="training-content">
      <button class="back" @click="goBack">‹ 返回</button>
      <view class="heading"><text>请选择陪练风格</text><small>不同风格将改变出牌推荐与牌局节奏</small></view>
      <view class="strategy-list">
        <button v-for="item in strategies" :key="item.value" class="strategy" :class="[item.value,{ active:selected===item.value }]" @click="selected=item.value">
          <text class="big-suits">{{ item.suits }}</text>
          <view class="strategy-title"><strong>{{ item.title }}</strong><text>{{ item.tag }}</text><i v-if="selected===item.value">✓</i></view>
          <text class="english">{{ item.english }}</text>
          <text class="desc">{{ item.desc }}</text>
        </button>
      </view>
      <button class="start" :class="{ enabled:selected }" :disabled="!selected || store.loading" @click="start">
        <text>{{ store.loading ? '正在准备牌局…' : (selected ? '开始对局 →' : '请选择一种风格') }}</text><i>♠ ♥ ♦ ♣</i>
      </button>
    </main>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { useGameStore } from '@/store/game'
const store=useGameStore();const selected=ref('balanced')
const strategies=[
  {value:'aggressive',title:'激进型',english:'AGGRESSIVE',tag:'高风险 · 高回报',suits:'♠ ♥',desc:'主动出击，快速清牌，节奏凌厉。适合追求主导权和高压牌风的玩家。'},
  {value:'balanced',title:'均衡型',english:'BALANCED',tag:'稳健 · 全面',suits:'♦ ♣',desc:'攻守兼备，灵活应变，顺势而为。适合想全面提升综合牌力的玩家。'},
  {value:'conservative',title:'保守型',english:'CONSERVATIVE',tag:'低风险 · 稳定',suits:'♣ ♠',desc:'稳扎稳打，控制风险，等待时机。适合注重胜率稳定性的玩家。'}]
const goBack=()=>uni.navigateBack()
const start=async()=>{await store.beginTraining(selected.value);uni.navigateTo({url:'/pages/game/index'})}
</script>

<style scoped lang="scss">
.training-page{position:relative;min-height:100vh;overflow:hidden;background:linear-gradient(170deg,#0c0814,#110620 52%,#0c0814);color:#e8e0f0}.ambient{position:absolute;top:-120rpx;left:50%;width:900rpx;height:500rpx;transform:translateX(-50%);background:radial-gradient(ellipse,rgba(130,0,80,.22),transparent 70%)}.watermark{position:absolute;right:-80rpx;top:32%;color:rgba(199,125,255,.045);font-size:110rpx;transform:rotate(-12deg)}.training-content{position:relative;z-index:2;width:100%;max-width:760rpx;margin:auto;padding:70rpx 48rpx}.back{padding:8rpx 0;border:0;background:none;color:rgba(199,125,255,.62);font-size:25rpx}.heading{margin-top:42rpx;display:flex;flex-direction:column}.heading>text{color:#c2185b;font-size:43rpx;font-weight:900}.heading small{margin-top:12rpx;color:rgba(232,224,240,.35);font-size:23rpx}.strategy-list{margin-top:50rpx;display:flex;flex-direction:column;gap:26rpx}.strategy{position:relative;min-height:210rpx;padding:38rpx 40rpx;border:0;border-radius:38rpx;overflow:hidden;text-align:left;color:#fff;transition:.2s;background:linear-gradient(145deg,rgba(70,20,110,.5),rgba(35,10,60,.7));box-shadow:0 10rpx 34rpx rgba(0,0,0,.3)}.strategy.aggressive{background:linear-gradient(145deg,rgba(120,0,60,.52),rgba(60,0,30,.7))}.strategy.conservative{background:linear-gradient(145deg,rgba(30,35,70,.6),rgba(15,18,40,.75))}.strategy.active{transform:scale(1.012);box-shadow:0 0 0 3rpx rgba(199,125,255,.55),0 18rpx 60rpx rgba(155,79,202,.28)}.strategy.aggressive.active{box-shadow:0 0 0 3rpx rgba(212,0,106,.55),0 18rpx 60rpx rgba(212,0,106,.3)}.big-suits{position:absolute;right:-18rpx;top:28rpx;color:rgba(255,255,255,.08);font-size:100rpx;transform:rotate(-8deg)}.strategy-title{position:relative;z-index:2;display:flex;align-items:center;gap:18rpx}.strategy-title strong{font-size:36rpx}.strategy-title text{padding:5rpx 15rpx;border-radius:99rpx;color:#c77dff;background:rgba(199,125,255,.1);font-size:19rpx}.aggressive .strategy-title text{color:#ff6b9d;background:rgba(212,0,106,.13)}.conservative .strategy-title text{color:#9cadd7}.strategy-title i{margin-left:auto;color:#c77dff;font-style:normal;font-weight:900}.english{position:relative;z-index:2;display:block;margin-top:12rpx;color:rgba(232,224,240,.28);font-size:20rpx;letter-spacing:3rpx}.desc{position:relative;z-index:2;display:block;max-width:80%;margin-top:17rpx;color:rgba(232,224,240,.6);font-size:24rpx;line-height:1.65}.start{position:relative;width:100%;margin-top:54rpx;padding:32rpx;border:0;border-radius:999rpx;overflow:hidden;color:rgba(255,255,255,.2);background:rgba(255,255,255,.06);font-size:31rpx;font-weight:800}.start.enabled{color:#fff;background:linear-gradient(135deg,#9b006e,#d4006a 62%,#e91e8c);box-shadow:0 16rpx 54rpx rgba(212,0,106,.35)}.start text{position:relative;z-index:2}.start i{position:absolute;right:34rpx;color:rgba(255,255,255,.08);font-size:45rpx;font-style:normal}@media(min-width:768px){.training-content{max-width:1100px}.strategy-list{display:grid;grid-template-columns:repeat(3,1fr)}.strategy{min-height:250px}.desc{max-width:100%}}
</style>
