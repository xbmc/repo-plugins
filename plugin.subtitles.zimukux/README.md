这是一个源自 [https://github.com/taxigps/xbmc-addons-chinese/tree/master/service.subtitles.zimuku](https://github.com/taxigps/xbmc-addons-chinese/tree/master/service.subtitles.zimuku)（原插件）的插件，用于从「字幕库」这个网站下载字幕，目前只适用于 [Kodi V19](https://kodi.tv) 以上版本。
  
现在 Kodi 上面基本就 Shooter 和字幕库两个插件能下载字幕了（其实 SubHD 最好，但他现在有一些验证手段，可能 Kodi 插件没法搞定），而 Shooter 好像数量不行，特别是美剧基本没有新的，所以留给我们 Kodi 党就只有一个选择，所以有问题只好自己解决……那为啥要 fork 呢？
1. 原插件没法配置网站的地址，而字幕库这网站好像经常变换网址，不能每次都去发版吧
2. 字幕库的设计很简单，搜索关键词的话就把相关字幕全部列出来，没法限定哪一集；原插件也继承了这个设计，所以找到对应的字幕很麻烦（用过 Kodi 的朋友看到此处应该起立送上掌声了）
3. 好像就两点  

所以这个新插件就解决了上述问题，大家有啥问题就尽量拨冗来提 Issue（PR 更好……），然后我也准备把它提交给官方
我这个版本继承了 GPLv2 的 license，希望原作者没啥意见。有啥意见的话请来找我……
