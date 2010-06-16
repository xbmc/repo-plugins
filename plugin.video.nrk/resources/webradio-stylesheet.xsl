<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
  <html>
  <body>
  <h2>NRK web radio streams</h2>
  <hr/>
  <xsl:for-each select="radio/channel">
    <h3><xsl:value-of select="title"/></h3>
    <table border="1">
      <tr bgcolor="#9acd32">
        <th>format</th>
        <th>bitrate (kbps)</th>
        <th>link</th>
      </tr>
      <xsl:for-each select="stream">
        <tr>
          <td><xsl:value-of select="format"/></td>
          <td><xsl:value-of select="bitrate"/></td>
          <td><xsl:value-of select="link"/></td>
        </tr>
      </xsl:for-each>
    </table>
  </xsl:for-each>
  </body>
  </html>
</xsl:template>

</xsl:stylesheet> 
