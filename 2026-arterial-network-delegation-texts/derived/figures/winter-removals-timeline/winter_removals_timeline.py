#!/usr/bin/env python3
"""Protected bike facilities on Montréal's arterial network taken out of winter service, by winter, and who decided.
Sources: Outremont file 1255069030 and by-laws AO-548 to AO-722; the City's arterial-network layer (2023) and cycling data
of October 14, 2026; the Ahuntsic-Cartierville notice of October 28, 2026; borough file 1266880005; City council minutes,
January 2020 to September 2026. Colours: categorical slots checked for colour-vision deficiency.
Usage: python3 winter_removals_timeline.py  (needs matplotlib)"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
SURF="#fcfcfb"; INK="#1f1f1d"; MUTED="#6b6a64"
KEPT="#2a78d6"; PARK="#eb6834"; NOCL="#1baf7a"; NONE="#e9e8e3"
W=["2019–20","2020–21","2021–22","2022–23","2023–24","2024–25","2025–26","2026–27"]
# state codes: K kept in winter service, P out of service with parking allowed in its place, N not cleared, A announced (P, hatched), ? no information, - not built
TEXT={
 "en":{"r1":"Avenue Lajoie, Outremont","r1s":"about 200 m, partly arterial","r1w":"Borough by-laws; a standing\nwinter rule since April 2026",
  "r2":"District central, Ahuntsic-Cartierville","r2s":"about 3.6 km, nearly all arterial","r2w":"Notice to residents;\nno council resolution found",
  "r3":"Rue de Terrebonne, CDN-NDG","r3s":"2.45 km, all arterial; built 2024","r3w":"Offer to City council voted Nov. 2, 2026;\nnot on the agenda posted for Dec. 1",
  "none":"none found","by":"Decided by","vote":"City council vote","kept":"kept","park":"parking","ann":"announced",
  "title":"Protected bike lanes on Montréal's arterial network converted to parking for the winter: no City council vote found",
  "sub":"Each cell is one winter. Cases found so far; not a complete inventory. Off-street and gravel multi-use paths are not included.",
  "l1":"Protected lane kept in winter","l2":"Out of winter service, parking allowed in its place","l3":"Same, announced for this winter","l4":"No information found","l5":"Not yet built",
  "src":"Sources: Outremont file 1255069030 and by-laws AO-548 to AO-722; City arterial-network and cycling data;\nAhuntsic-Cartierville notice, Oct. 28, 2026; CDN-NDG file 1266880005; City council minutes, Jan. 2020 to Sept. 2026; CDN-NDG agenda of Dec. 1, 2026.  November 28, 2026."},
 "fr":{"r1":"Avenue Lajoie, Outremont","r1s":"environ 200 m, en partie artériel","r1w":"Règlements d'arrondissement; règle\nhivernale permanente depuis avril 2026",
  "r2":"District central, Ahuntsic-Cartierville","r2s":"environ 3,6 km, presque tout artériel","r2w":"Avis au voisinage;\naucune résolution du conseil trouvée",
  "r3":"Rue de Terrebonne, CDN-NDG","r3s":"2,45 km, tout artériel; aménagée en 2024","r3w":"Offre au conseil municipal votée le\n2 nov. 2026; pas à l'ordre du jour\npublié du 1er déc.",
  "none":"aucun trouvé","by":"Décidé par","vote":"Vote du conseil municipal","kept":"gardée","park":"stationn.","ann":"annoncé",
  "title":"Pistes cyclables protégées du réseau artériel de Montréal converties en stationnement l'hiver : aucun vote du conseil municipal trouvé",
  "sub":"Chaque case est un hiver. Cas trouvés à ce jour; inventaire non exhaustif. Les sentiers hors rue et en gravier ne sont pas inclus.",
  "l1":"Piste protégée gardée l'hiver","l2":"Hors service l'hiver, stationnement permis à sa place","l3":"Idem, annoncé pour cet hiver","l4":"Aucune information trouvée","l5":"Pas encore aménagée",
  "src":"Sources : dossier 1255069030 et règlements AO-548 à AO-722 d'Outremont; données de la Ville sur le réseau artériel et le réseau cyclable;\navis d'Ahuntsic-Cartierville, 28 oct. 2026; dossier 1266880005 de CDN-NDG; procès-verbaux du conseil municipal, janv. 2020 à sept. 2026; ordre du jour de CDN-NDG du 1er déc. 2026.  28 novembre 2026."},
}
for lang,T in TEXT.items():
    ROWS=[
     (T["r1"],T["r1s"],"K K P P K K P P".split(),T["r1w"],T["none"]),
     (T["r2"],T["r2s"],"? ? ? ? ? ? ? P".split(),T["r2w"],T["none"]),
     (T["r3"],T["r3s"],"- - - - - K K A".split(),T["r3w"],T["none"]),
    ]
    fig,ax=plt.subplots(figsize=(15.5,5.6),dpi=160); fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
    x0=5.7; cw=1.0; ch=0.62; gap=0.06
    for j,w in enumerate(W): ax.text(x0+j*cw+cw/2,len(ROWS)+0.08,w,ha="center",va="bottom",fontsize=8.6,color=INK)
    ax.text(x0+len(W)*cw+0.25,len(ROWS)+0.08,T["by"],ha="left",va="bottom",fontsize=9.5,color=INK,weight="bold")
    ax.text(x0+len(W)*cw+4.7,len(ROWS)+0.08,T["vote"],ha="left",va="bottom",fontsize=9.5,color=INK,weight="bold")
    LAB={"K":T["kept"],"P":T["park"],"N":"","A":T["ann"],"?":"","-":""}
    for i,(name,sub,st,who,vote) in enumerate(ROWS):
        y=len(ROWS)-1-i
        ax.text(0,y+ch/2+0.10,name,ha="left",va="center",fontsize=10.5,color=INK,weight="bold")
        ax.text(0,y+ch/2-0.17,sub,ha="left",va="center",fontsize=8.8,color=MUTED)
        for j,s in enumerate(st):
            col={"K":KEPT,"P":PARK,"N":NOCL,"A":PARK,"?":NONE,"-":SURF}[s]
            p=FancyBboxPatch((x0+j*cw+gap/2,y+gap/2),cw-gap,ch-gap,boxstyle="round,pad=0,rounding_size=0.05",fc=col,ec=("#bdbcb5" if s=="-" else "none"),lw=0.8,ls=(":" if s=="-" else "-"),hatch=("////" if s=="A" else None))
            if s=="A": p.set_edgecolor(SURF); p.set_linewidth(0)
            ax.add_patch(p)
            if LAB[s]:
                ax.text(x0+j*cw+cw/2,y+ch/2,LAB[s],ha="center",va="center",fontsize=(6.9 if s=="A" else 7.8),linespacing=0.95,color=("white" if s in "KP" else INK),weight="bold",
                        bbox=(dict(fc=SURF,ec="none",pad=1.5) if s=="A" else None))
        ax.text(x0+len(W)*cw+0.25,y+ch/2,who,ha="left",va="center",fontsize=8.8,color=INK,wrap=True)
        ax.text(x0+len(W)*cw+4.7,y+ch/2,vote,ha="left",va="center",fontsize=9.5,color=INK,weight="bold")
    ax.set_xlim(-0.1,x0+len(W)*cw+6.7); ax.set_ylim(-2.3,len(ROWS)+1.2); ax.axis("off")
    ax.text(0,len(ROWS)+0.95,T["title"],fontsize=13,weight="bold",color=INK,va="top")
    ax.text(0,len(ROWS)+0.55,T["sub"],fontsize=9.5,color=MUTED,va="top")
    h=[Patch(fc=KEPT,label=T["l1"]),Patch(fc=PARK,label=T["l2"]),
       Patch(fc=PARK,hatch="////",ec=SURF,label=T["l3"]),
       Patch(fc=NONE,label=T["l4"]),Patch(fc=SURF,ec="#bdbcb5",ls=":",label=T["l5"])]
    ax.legend(handles=h,loc="lower left",bbox_to_anchor=(0.0,0.13),ncol=5,frameon=False,fontsize=8.8,handlelength=1.6,columnspacing=1.6,labelcolor=INK)
    ax.text(0,-2.25,T["src"],
            fontsize=7.6,color=MUTED,ha="left",va="bottom")
    for ext in ("png","svg"): fig.savefig(f"winter_removals_timeline_{lang}.{ext}",facecolor=SURF,bbox_inches="tight")
    plt.close(fig)

print("ok")
