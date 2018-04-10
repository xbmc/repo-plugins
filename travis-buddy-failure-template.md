## Travis Buddy
Hey **{{author}}**, 
Please review the following log in order to understand the failure reason. There might also be some helpful tips along the way. 
It'll be awesome if you fix what's wrong and commit the changes.

{{#jobs}}
### {{displayName}}
{{#scripts}}
<details>
  <summary>
    <strong>
     {{command}}
    </strong>
  </summary>

```
{{&contents}}
```
</details>
<br />
{{/scripts}}
{{/jobs}}
