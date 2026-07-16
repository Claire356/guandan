<template>
  <view class="home-page safe-bottom">
    <view class="ambient ambient-top"></view><view class="ambient ambient-bottom"></view>
    <view class="suit-stars">♠　♥　♦　♣</view>
    <main class="home-content">
      <text class="brand-kicker">AI · GUANDAN COACH</text>
      <text class="brand-title">AI 掼蛋教练</text>
      <text class="brand-subtitle">智能分析 · 提升牌技 · 登顶段位</text>

      <section class="win-section">
        <text class="section-kicker">游戏胜率 · 近30局</text>
        <view class="card-fan" aria-label="近30局胜率73%">
          <view v-for="(won,index) in fanCards" :key="index" class="fan-card" :class="{ won }" :style="fanStyle(index)">
            <text>{{ won ? (index % 2 ? '♦' : '♥') : '' }}</text>
          </view>
        </view>
        <view class="win-number"><text>73</text><small>%</small></view>
        <view class="stats">
          <view><strong>158</strong><text>总对局</text></view>
          <view><strong>11</strong><text>连胜最高</text></view>
          <view><strong class="pink">19</strong><text>本周胜</text></view>
        </view>
      </section>

      <view class="divider"></view>
      <view class="home-actions">
        <button class="action-card primary" @click="goTraining">
          <view><strong>开始测试</strong><text>AI 实战牌局分析</text></view><text class="arrow">›</text>
          <text class="action-suits">♠ ♥ ♦ ♣</text>
        </button>
        <button class="action-card secondary" @click="goHistory">
          <view><strong>历史报告</strong><text>查看对局复盘与分析</text></view><text class="arrow">›</text>
          <text class="action-suits">♣ ♠ ♥ ♦</text>
        </button>
      </view>
      <text class="online-tip">♠ AI 教练在线 · 随时为您服务 ♠</text>
    </main>
  </view>
</template>

<script setup>
const goTraining = () => uni.navigateTo({ url: '/pages/training/index' })
const goHistory = () => uni.navigateTo({ url: '/pages/history/index' })
const fanCards = [true,true,true,true,true,true,true,false,false,false]
const fanStyle = index => {
  const offset = index - 4.5
  return { transform: `translateX(${offset * 30}rpx) translateY(${Math.abs(offset) * 5}rpx) rotate(${offset * 6}deg)` }
}
</script>

<style scoped lang="scss">
.home-page{position:relative;min-height:100vh;overflow:hidden;background:linear-gradient(170deg,#0c0814 0%,#110620 52%,#0c0814 100%);color:#e8e0f0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}.ambient{position:absolute;border-radius:50%;pointer-events:none}.ambient-top{top:-150rpx;left:50%;width:900rpx;height:520rpx;transform:translateX(-50%);background:radial-gradient(ellipse,rgba(150,0,90,.24),transparent 70%)}.ambient-bottom{right:-180rpx;bottom:-180rpx;width:650rpx;height:650rpx;background:radial-gradient(circle,rgba(90,0,140,.2),transparent 70%)}.suit-stars{position:absolute;top:18%;left:0;right:0;text-align:center;color:rgba(199,125,255,.055);font-size:110rpx;letter-spacing:32rpx;transform:rotate(-7deg)}.home-content{position:relative;z-index:2;width:100%;max-width:760rpx;margin:0 auto;padding:70rpx 56rpx 60rpx;display:flex;flex-direction:column;align-items:center}.brand-kicker{color:rgba(199,125,255,.55);font-size:21rpx;font-weight:600;letter-spacing:6rpx}.brand-title{margin-top:22rpx;color:#c2185b;font-size:54rpx;font-weight:900;letter-spacing:-2rpx}.brand-subtitle{margin-top:14rpx;color:rgba(232,224,240,.38);font-size:25rpx}.win-section{width:100%;margin-top:60rpx;text-align:center}.section-kicker{color:rgba(199,125,255,.5);font-size:21rpx;letter-spacing:5rpx}.card-fan{position:relative;width:450rpx;height:150rpx;margin:36rpx auto 0}.fan-card{position:absolute;left:50%;bottom:0;width:72rpx;height:108rpx;display:flex;align-items:center;justify-content:center;border:1rpx solid rgba(255,255,255,.08);border-radius:12rpx;background:rgba(255,255,255,.055);transform-origin:bottom center;color:rgba(255,200,220,.9);font-size:30rpx;box-shadow:0 4rpx 16rpx rgba(0,0,0,.2)}.fan-card.won{border-color:rgba(255,100,150,.38);background:linear-gradient(160deg,#c2185b,#880e4f);box-shadow:0 10rpx 30rpx rgba(194,24,91,.35)}.win-number{margin-top:8rpx;display:flex;align-items:flex-start;justify-content:center}.win-number>text{font-size:150rpx;font-weight:950;line-height:1;letter-spacing:-10rpx;background:linear-gradient(135deg,#e8d0ff,#c77dff 35%,#d4006a 82%);background-clip:text;-webkit-background-clip:text;color:transparent}.win-number small{margin:16rpx 0 0 10rpx;color:rgba(199,125,255,.55);font-size:50rpx;font-weight:800}.stats{display:flex;justify-content:center;gap:70rpx;margin-top:30rpx}.stats view{display:flex;flex-direction:column}.stats strong{color:#c77dff;font-size:40rpx}.stats strong.pink{color:#ff6b9d}.stats text{margin-top:7rpx;color:rgba(232,224,240,.4);font-size:21rpx}.divider{width:60%;height:1rpx;margin:72rpx 0;background:linear-gradient(90deg,transparent,rgba(199,125,255,.2),transparent)}.home-actions{width:100%;display:flex;flex-direction:column;gap:22rpx}.action-card{position:relative;width:100%;min-height:120rpx;padding:24rpx 38rpx;border:0;border-radius:999rpx;overflow:hidden;display:flex;align-items:center;text-align:left}.action-card view{position:relative;z-index:2;flex:1;display:flex;flex-direction:column}.action-card strong{color:#fff;font-size:31rpx}.action-card view text{margin-top:5rpx;color:rgba(255,255,255,.56);font-size:21rpx}.action-card.primary{background:linear-gradient(135deg,#9b006e,#d4006a 62%,#e91e8c);box-shadow:0 16rpx 60rpx rgba(212,0,106,.35)}.action-card.secondary{background:rgba(199,125,255,.09)}.action-card.secondary strong{color:#e8d0ff}.action-card.secondary view text{color:rgba(199,125,255,.45)}.arrow{position:relative;z-index:2;color:rgba(255,255,255,.65);font-size:42rpx}.action-suits{position:absolute;right:42rpx;color:rgba(255,255,255,.075);font-size:48rpx;letter-spacing:-8rpx}.online-tip{margin-top:60rpx;color:rgba(199,125,255,.28);font-size:20rpx;letter-spacing:3rpx}@media(min-width:768px){.home-content{padding-top:50px}.win-section{margin-top:34px}.divider{margin:38px 0}.home-actions{max-width:540px}}
</style>
