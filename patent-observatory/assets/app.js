/* ISTAT-CNR Patent Observatory — static, dependency-free application logic.
   Input data are generated from the user's notebook CSVs; no live model inference.
   Plotly is bundled locally, so it works after Colab disconnects.
*/
(() => {
 'use strict';
 const D=window.PATENT_DATA, ORDER=D.meta.model_order, MAPS=new Set(window.AVAILABLE_MAPS||[]);
 const $=id=>document.getElementById(id);
 const nf=(n,p=3)=>n===null||n===undefined||!Number.isFinite(Number(n))?'—':Number(n).toFixed(p);
 const pct=(n,p=1)=>n===null||n===undefined?'—':(100*Number(n)).toFixed(p)+'%';
 const escapeHtml=(x)=>String(x===null||x===undefined?'':x).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const title=m=>D.meta.models[m]?.display||m;
 const isFull=(r)=>r.n_patents===63968;
 const C={teal:'#008c98',blue:'#3b83b5',gold:'#dfaa60',purple:'#8566b5',green:'#369176',line:'#dce5ee',ink:'#233e52'};
 const roleColors={central:'#007f90',random:'#4a9b76',peripheral:'#e8a250',boundary:'#8f70c1'};
 const roleShapes={central:'circle',random:'square',peripheral:'diamond',boundary:'x'};
 const layoutBase={paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'Arial, sans-serif',size:11,color:'#4d6275'},margin:{l:50,r:17,t:18,b:70},hoverlabel:{bgcolor:'#1e4050',font:{color:'white'}},showlegend:true,legend:{orientation:'h',x:0,y:1.2},xaxis:{gridcolor:'#eaf0f4',zeroline:false},yaxis:{gridcolor:'#eaf0f4',zeroline:false}};
 function chart(id,traces,layout={}) {
   const node=$(id);if(!node)return;
   const opts={...layoutBase,...layout,margin:{...layoutBase.margin,...(layout.margin||{})},xaxis:{...layoutBase.xaxis,...(layout.xaxis||{})},yaxis:{...layoutBase.yaxis,...(layout.yaxis||{})}};
   Plotly.react(node,traces,opts,{responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d','toImage']});
 }
 function selectModels(id){$(id).innerHTML=ORDER.map(m=>`<option value="${escapeHtml(m)}">${escapeHtml(title(m))}</option>`).join('');}
 const fullFor=(k)=>D.full.filter(r=>r.k==k);
 const pilotFor=(k)=>D.pilot.filter(r=>r.k==k);
 function sortModelRows(rows,metric){return [...rows].sort((a,b)=>(b[metric]||0)-(a[metric]||0));}
 function fancyLabel(m){return title(m);}
 function horizBar(id,rows,xKey,label='Value',color=C.teal,opts={}){
   chart(id,[{type:'bar',orientation:'h',x:rows.map(r=>r[xKey]),y:rows.map(r=>fancyLabel(r.model)),name:label,marker:{color},hovertemplate:'%{y}: %{x:.4f}<extra></extra>'}],
     {margin:{l:150,r:20,t:10,b:36},showlegend:false,yaxis:{autorange:'reversed',gridcolor:'transparent'},xaxis:{rangemode:'tozero',title:{text:opts.xTitle||'',font:{size:10}}}});
 }
 function overview(){const sorted=sortModelRows(fullFor(16),'WIPO_AMI_mean');horizBar('overview-ami',sorted,'WIPO_AMI_mean','WIPO AMI',C.teal);const pairs=D.contrast.map(r=>({...r})).sort((a,b)=>b.mean_paired_difference-a.mean_paired_difference);horizBar('overview-pairs',pairs,'mean_paired_difference','Same-field advantage',C.blue);}
 function sample(){
   const s=D.sectors;
   chart('sample-sectors',[{type:'bar',orientation:'h',x:s.map(x=>x.sampled_rows),y:s.map(x=>x.sector),marker:{color:[C.blue,C.purple,C.teal,C.gold]},customdata:s.map(x=>x.fields),hovertemplate:'%{y}: %{x:,} sampled rows, %{customdata} fields<extra></extra>'}],{margin:{l:175,r:15,t:7,b:35},showlegend:false,yaxis:{autorange:'reversed',gridcolor:'transparent'},xaxis:{title:{text:'Field-level selections',font:{size:10}}}});
   const offices=D.offices.slice(0,11);
   chart('sample-offices',[{type:'bar',x:offices.map(x=>x.office),y:offices.map(x=>x.count),marker:{color:offices.map(x=>x.office==='CN'?C.teal:C.blue)},text:offices.map(x=>x.share_pct+'%'),textposition:'outside',cliponaxis:false,hovertemplate:'%{x}: %{y:,} publications<extra></extra>'}],{margin:{l:58,r:18,t:32,b:38},showlegend:false,yaxis:{rangemode:'tozero',title:{text:'Publications',font:{size:10}}}});
 }
 function models(){
   const k=Number($('model-k').value),metric=$('model-metric').value,full=sortModelRows(fullFor(k),metric), names=full.map(x=>x.model);
   const pilotBy=new Map(pilotFor(k).map(r=>[r.model,r]));
   const lab={'WIPO_AMI_mean':'WIPO AMI','silhouette_mean':'Cosine silhouette','seed_ARI_mean':'Seed stability ARI','office_AMI_mean':'Office AMI','largest_cluster_share_mean':'Largest cluster share'}[metric];
   $('model-chart-title').textContent=lab+': pilot versus full corpus';
   chart('model-main-chart',[
    {type:'bar',name:'Pilot · 6,400',x:names.map(title),y:names.map(m=>pilotBy.get(m)?.[metric]),marker:{color:C.gold},hovertemplate:'%{x}<br>Pilot: %{y:.4f}<extra></extra>'},
    {type:'bar',name:'Full · 63,968',x:names.map(title),y:full.map(r=>r[metric]),marker:{color:C.teal},hovertemplate:'%{x}<br>Full: %{y:.4f}<extra></extra>'}
   ],{barmode:'group',margin:{l:53,r:18,t:30,b:115},xaxis:{tickangle:-35,gridcolor:'transparent'},yaxis:{rangemode:'tozero'},legend:{orientation:'h',x:0,y:1.13}});
   $('model-benchmark-table').querySelector('tbody').innerHTML=full.map(r=>`<tr><td>${escapeHtml(title(r.model))}</td><td>${nf(r.WIPO_AMI_mean)}</td><td>${nf(r.silhouette_mean)}</td><td>${nf(r.seed_ARI_mean)}</td><td class="${r.office_AMI_mean>.1?'value-warn':''}">${nf(r.office_AMI_mean)}</td><td>${pct(r.largest_cluster_share_mean)}</td></tr>`).join('');
   $('model-spec-table').querySelector('tbody').innerHTML=ORDER.map(m=>{let x=D.meta.models[m];return `<tr><td>${escapeHtml(title(m))}</td><td>${x.dim}</td><td>${x.max_length}</td><td>${x.truncated===null?'Chunked':x.truncated}</td></tr>`;}).join('');
   const A=D.cross_ari[k===8?'full_8':'full_16'];
   chart('cross-model-chart',[{type:'heatmap',x:A.names.map(title),y:A.names.map(title),z:A.values,zmin:0,zmax:1,colorscale:[[0,'#f6fafc'],[.45,'#a6d9d5'],[1,'#087483']],hovertemplate:'%{y} vs %{x}<br>ARI %{z:.3f}<extra></extra>',colorbar:{title:{text:'ARI',side:'right'},thickness:12,outlinewidth:0}}],{margin:{l:135,b:125,r:80,t:18},xaxis:{tickangle:-40,side:'bottom'},yaxis:{autorange:'reversed',scaleanchor:'x',scaleratio:1},showlegend:false});
 }
 function robustness(){
   const x=D.k_means_curve.map(r=>r.k_requested);
   chart('robust-k-chart',[
    {type:'scatter',mode:'lines+markers',name:'WIPO AMI',x,y:D.k_means_curve.map(r=>r.WIPO_AMI),line:{color:C.teal,width:3},marker:{size:7}},
    {type:'scatter',mode:'lines+markers',name:'Silhouette',x,y:D.k_means_curve.map(r=>r.silhouette),line:{color:C.gold,width:3},marker:{size:7}}
   ],{xaxis:{title:{text:'K clusters',font:{size:11}},tickmode:'array',tickvals:x},margin:{l:49,r:15,b:50,t:25}});
   chart('robust-seed-chart',[{type:'scatter',mode:'lines+markers',x,y:D.k_means_curve.map(r=>r.seed_ARI),line:{color:C.blue,width:3},marker:{size:8},hovertemplate:'K=%{x}: ARI %{y:.3f}<extra></extra>'}],{showlegend:false,margin:{l:48,r:16,t:12,b:47},xaxis:{title:{text:'K clusters',font:{size:11}},tickmode:'array',tickvals:x},yaxis:{range:[0,1.05]}});
   const s=D.spherical_summary;
   chart('robust-spherical-chart',[
    {type:'bar',x:s.map(r=>'K='+r.k),y:s.map(r=>r.kmeans_AMI),name:'Ordinary',marker:{color:C.teal}},
    {type:'bar',x:s.map(r=>'K='+r.k),y:s.map(r=>r.spherical_AMI),name:'Spherical',marker:{color:C.blue}}
   ],{barmode:'group',margin:{l:50,r:18,t:24,b:45},yaxis:{rangemode:'tozero'}});
   const h=D.robust.filter(r=>r.method==='HDBSCAN'&&r.setting==='PCA50_mcs75_ms10');
   h.sort((a,b)=>b.coverage-a.coverage);
   horizBar('robust-hdbscan-chart',h,'coverage','Coverage',C.purple,{xTitle:'Share assigned (0–1)'});
   const pairs=D.contrast.map(r=>({...r,ci_pos:r.descriptive_bootstrap_high})).sort((a,b)=>b.mean_paired_difference-a.mean_paired_difference);
   chart('robust-pair-chart',[{type:'bar',orientation:'h',x:pairs.map(r=>r.mean_paired_difference),y:pairs.map(r=>title(r.model)),marker:{color:pairs.map(r=>r.mean_paired_difference>.2?C.teal:C.blue)},customdata:pairs.map(r=>r.fraction_positive),hovertemplate:'%{y}<br>Mean advantage: %{x:.4f}<br>Fraction positive: %{customdata:.1%}<extra></extra>'}],{margin:{l:158,r:20,t:15,b:44},showlegend:false,yaxis:{autorange:'reversed',gridcolor:'transparent'},xaxis:{rangemode:'tozero',title:{text:'Mean paired cosine-similarity advantage',font:{size:11}}}});
   chart('robust-abstract-chart',[{type:'bar',orientation:'h',y:D.abstract_experiment.map(r=>r.name),x:D.abstract_experiment.map(r=>r.ami),marker:{color:[C.teal,C.blue,C.gold,C.blue,C.gold]},hovertemplate:'%{y}: WIPO AMI %{x:.3f}<extra></extra>'}],{showlegend:false,margin:{l:128,r:12,t:6,b:30},yaxis:{autorange:'reversed'},xaxis:{range:[0,.36]}});
 }
 function composition(){
   const m=$('comp-model').value,k=Number($('comp-k').value),a=D.pilot_composition.filter(r=>r.model===m&&r.k===k).sort((x,y)=>x.cluster-y.cluster);
   if(!a.length)return;
   const clusters=a.map(r=>'C'+r.cluster),weightedCN=a.reduce((s,r)=>s+r.n*r.CN_share,0)/a.reduce((s,r)=>s+r.n,0);
   chart('comp-cn-chart',[{type:'bar',x:clusters,y:a.map(r=>100*r.CN_share),marker:{color:a.map(r=>r.CN_share>.9?C.gold:C.teal)},hovertemplate:'%{x}: %{y:.1f}% CN<extra></extra>'}],{margin:{l:48,r:9,t:18,b:45},showlegend:false,yaxis:{range:[0,105],ticksuffix:'%'},shapes:[{type:'line',x0:-.5,x1:clusters.length-.5,y0:100*weightedCN,y1:100*weightedCN,line:{color:C.purple,dash:'dot',width:2}}]});
   chart('comp-wipo-chart',[{type:'bar',x:clusters,y:a.map(r=>r.effective_WIPO_fields),marker:{color:C.blue},hovertemplate:'%{x}: %{y:.1f} effective fields<extra></extra>'}],{margin:{l:48,r:9,t:18,b:45},showlegend:false,yaxis:{rangemode:'tozero',title:{text:'Effective fields',font:{size:10}}}});
   $('comp-table').querySelector('tbody').innerHTML=a.map(r=>`<tr><td>C${r.cluster}</td><td>${r.n.toLocaleString()}</td><td>${pct(r.cluster_share)}</td><td>${String(r.top_WIPO_field_number).padStart(2,'0')}</td><td>${pct(r.top_WIPO_field_share)}</td><td>${nf(r.effective_WIPO_fields,1)}</td><td class="${r.CN_share>.95?'value-warn':''}">${pct(r.CN_share)}</td></tr>`).join('');
 }
 let explorerView='umap',selectedPatent=null,explorerRows=[];
 function initExplorer(){
   selectModels('explore-model');selectModels('comp-model');
   const root=$('explore-cluster');root.innerHTML='<option value="all">All clusters</option>';
   $('explore-model').value='sbert-adapt-ub';$('comp-model').value='sbert-adapt-ub';
 }
 function getRows(){const cohort=$('explore-cohort').value,m=$('explore-model').value,k=Number($('explore-k').value),cluster=$('explore-cluster').value;
   return (cohort==='pilot'?D.review:D.full_review).filter(r=>r.model===m&&r.k===k&&(cluster==='all'||r.cluster==cluster));
 }
 function setPatent(r){
   if(!r)return;
   selectedPatent=r;
   $('patent-details').innerHTML=`<div class="selected-detail"><h3>${escapeHtml(r.title_clean||'Untitled patent')}</h3><div class="d-meta"><span>${escapeHtml(r.publication_number)}</span><span>Office ${escapeHtml(r.office||'Unknown')}</span><span>WIPO ${escapeHtml(r.wipo_field_number)}</span><span>Cluster ${escapeHtml(r.cluster)}</span><span>${escapeHtml(r.selection_type)}</span></div><p>${escapeHtml(r.abstract_clean||'Abstract not available.')}</p></div>`;
   const id=(r.publication_number||'').replace(/[^a-zA-Z0-9]/g,'');
   const link=$('patent-link');link.href='https://patents.google.com/patent/'+encodeURIComponent(id)+'/en';link.classList.remove('hidden');
 }
 function selectClusterOptions(){
   const k=Number($('explore-k').value),old=$('explore-cluster').value;
   const options=Array.from({length:k},(_,i)=>`<option value="${i}">Cluster ${i}</option>`).join('');
   $('explore-cluster').innerHTML='<option value="all">All clusters</option>'+options;
   if(old!=='all'&&Number(old)<k)$('explore-cluster').value=old;
 }
 function explorer(){
   const cohort=$('explore-cohort').value,k=Number($('explore-k').value),model=$('explore-model').value;
   if(cohort==='full'&&k===16){$('explore-k').value='8';selectClusterOptions();}
   $('explore-k').querySelector('option[value="16"]').disabled=(cohort==='full');
   explorerRows=getRows();
   const available=MAPS.has(model),mapNotice=available?`Actual 2,400-point pilot UMAP available for ${escapeHtml(title(model))}. It does not display the full 63,968 points or full-corpus K-Means fit.`:`No UMAP HTML imported for ${escapeHtml(title(model))} yet. All quantitative results and clickable distance diagnostics are already available. The missing map was saved by Notebook 14 to your Drive.`;
   $('map-banner').innerHTML=`<strong>${cohort==='pilot'?'Pilot examples':'Full-corpus examples'}:</strong> ${explorerRows.length} selected patents shown in diagnostics. ${mapNotice}`;
   ['umap','diagnostic','cards'].forEach(view=>{$(view+'-panel').classList.toggle('hidden',view!==explorerView)});
   if(explorerView==='umap'){
     if(available){
      const path=`maps/14_patent_map_${model}.html`;
      if($('umap-container').dataset.currentMap!==path){
       $('umap-container').innerHTML=`<iframe title="Interactive UMAP patent map for ${escapeHtml(title(model))}" loading="lazy" src="${path}"></iframe>`;
       $('umap-container').dataset.currentMap=path;
      }
     } else {
      $('umap-container').dataset.currentMap='';
      $('umap-container').innerHTML=`<div class="map-info"><b>UMAP coordinates not bundled for this model</b><p>This is a <em>data availability</em> limitation of the uploaded files, not a missing computation. Notebook 14 saved <code>14_patent_map_${escapeHtml(model)}.html</code> on your Drive. Use <code>15_complete_dashboard_maps_colab.ipynb</code> in the ZIP to import all nine HTML files without recomputing embeddings or UMAP.</p><button class="outline-btn" id="switch-to-diagnostic" type="button">Show interactive centroid-distance diagnostic</button></div>`;
      $('switch-to-diagnostic')?.addEventListener('click',()=>setExplorerView('diagnostic'));
     }
   } else if(explorerView==='diagnostic') renderPatentDiagnostic();
   else renderCards();
 }
 function renderPatentDiagnostic(){
   const isPilot=$('explore-cohort').value==='pilot';
   $('diagnostic-caption').textContent=isPilot?'Pilot example patents: X = percentile of centroid distance within cluster; Y = distance gap to second centroid (smaller = more ambiguous).':'Full-corpus example patents: X = raw centroid distance; Y = distance gap to second centroid (smaller = more ambiguous). These are not UMAP coordinates.';
   const roles=['central','random','peripheral','boundary'];
   const traces=roles.map(role=>{
     const rows=explorerRows.map((r,i)=>({r,i})).filter(v=>v.r.selection_type===role);
     return {type:'scatter',mode:'markers',name:role,x:rows.map(({r})=>isPilot?r.distance_percentile_within_cluster:r.distance_to_centroid),y:rows.map(({r})=>r.distance_gap_to_second_centroid),customdata:rows.map(({r,i})=>[i,r.publication_number,r.title_clean,r.cluster]),marker:{size:10,color:roleColors[role],symbol:roleShapes[role],opacity:.8,line:{width:0}},hovertemplate:'<b>%{customdata[1]}</b><br>%{customdata[2]}<br>Cluster: %{customdata[3]}<br>Gap: %{y:.4f}<extra>'+role+'</extra>'};
   });
   chart('patent-diagnostic-chart',traces,{margin:{l:68,r:16,t:20,b:68},xaxis:{title:{text:isPilot?'Centroid-distance percentile (within cluster)':'Raw centroid distance (model-specific)',font:{size:11}}},yaxis:{title:{text:'Second-centroid distance gap',font:{size:10}}},legend:{orientation:'h',x:0,y:1.15}});
   const div=$('patent-diagnostic-chart');div.removeAllListeners?.('plotly_click');
   div.on?.('plotly_click',e=>{const i=e.points[0]?.customdata?.[0];if(Number.isInteger(i))setPatent(explorerRows[i]);});
 }
 function renderCards(){
   const role=$('explore-role').value,q=$('explore-search').value.trim().toLowerCase();
   const rows=explorerRows.filter(r=>(role==='all'||r.selection_type===role)&&(!q||([r.title_clean,r.abstract_clean,r.publication_number,r.wipo_field_name].join(' ').toLowerCase().includes(q))));
   $('cards-count').textContent=`${rows.length} examples`;
   $('patent-cards').innerHTML=rows.slice(0,80).map(r=>{const i=explorerRows.indexOf(r);return `<button class="patent-card" data-patentindex="${i}" type="button"><div class="p-top"><code>${escapeHtml(r.publication_number)}</code><span class="role-label role-${escapeHtml(r.selection_type)}">${escapeHtml(r.selection_type)}</span></div><h4>${escapeHtml(r.title_clean||'Untitled')}</h4><p>${escapeHtml(r.abstract_clean||'')}</p></button>`;}).join('')||'<p class="subtle">No matches for the current filters.</p>';
   $('patent-cards').querySelectorAll('[data-patentindex]').forEach(button=>button.addEventListener('click',()=>{
    const idx=Number(button.dataset.patentindex);setPatent(explorerRows[idx]);$('patent-details').scrollIntoView({behavior:'smooth',block:'center'});
   }));
 }
 function setExplorerView(v){explorerView=v;document.querySelectorAll('[data-explore-view]').forEach(b=>b.classList.toggle('selected',b.dataset.exploreView===v));explorer();}
 function briefing(){
   const grouped=new Map();for(const r of D.quick_review){if(!grouped.has(r.model))grouped.set(r.model,[]);grouped.get(r.model).push(r);}
   $('quick-review').innerHTML=[...grouped].map(([m,rows])=>`<article class="quick-block"><h4>${escapeHtml(title(m))}</h4><small>Pilot cluster ${rows[0]?.cluster}, illustrative only</small>${rows.map(r=>`<button type="button" data-quick-id="${D.quick_review.indexOf(r)}"><span class="role-label role-${escapeHtml(r.selection_type)}">${escapeHtml(r.selection_type)}</span> <b>${escapeHtml(r.title_clean||r.publication_number)}</b></button>`).join('')}</article>`).join('');
   $('quick-review').querySelectorAll('[data-quick-id]').forEach(el=>el.addEventListener('click',()=>{
     const r=D.quick_review[Number(el.dataset.quickId)];
     $('explore-model').value=r.model;$('explore-cohort').value='pilot';$('explore-k').value='8';selectClusterOptions();$('explore-cluster').value=String(r.cluster);
     setExplorerView('cards');navigate('explorer');setPatent(r);
     $('patent-details').scrollIntoView({behavior:'smooth',block:'center'});
   }));
 }
 function methods(){
   $('method-caveats').innerHTML=D.caveats.map(t=>`<div class="caveat">${escapeHtml(t)}</div>`).join('');
 }
 const labelMap={overview:'Research answer',sample:'The sample',models:'Embedding comparison',robustness:'Clustering robustness',composition:'Cluster composition',explorer:'Explore patents',briefing:'Meeting briefing',methods:'Methods & sources'};
 let visit=new Set();
 const renderFunctions={overview,sample,models,robustness,composition,explorer,briefing,methods};
 function navigate(target){if(!$(target))return;
   document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p.id===target));
   document.querySelectorAll('.nav-link').forEach(p=>p.classList.toggle('active',p.dataset.target===target));
   $('page-label').textContent=labelMap[target]||target;
   $('sidebar').classList.remove('open');
   window.scrollTo({top:0,behavior:'instant'});
   requestAnimationFrame(()=>{try{renderFunctions[target]?.();visit.add(target)}catch(e){console.error('Rendering failed:',target,e);}});
 }
 function setup(){
   selectModels('comp-model');initExplorer();
   document.querySelectorAll('[data-target]').forEach(el=>el.addEventListener('click',()=>navigate(el.dataset.target)));
   document.querySelectorAll('[data-jump]').forEach(el=>el.addEventListener('click',()=>navigate(el.dataset.jump)));
   $('menu-toggle').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
   $('print-page').addEventListener('click',()=>window.print());
   $('model-k').addEventListener('change',models);$('model-metric').addEventListener('change',models);
   $('comp-model').addEventListener('change',composition);$('comp-k').addEventListener('change',composition);
   $('explore-model').addEventListener('change',explorer);
   $('explore-cohort').addEventListener('change',()=>{selectClusterOptions();explorer();});
   $('explore-k').addEventListener('change',()=>{selectClusterOptions();explorer();});
   $('explore-cluster').addEventListener('change',explorer);
   $('explore-role').addEventListener('change',renderCards);$('explore-search').addEventListener('input',renderCards);
   document.querySelectorAll('[data-explore-view]').forEach(el=>el.addEventListener('click',()=>setExplorerView(el.dataset.exploreView)));
   $('download-full-summary').addEventListener('click',()=>{window.location.href='downloads/13_model_K_summary(1).csv';});
   $('copy-conclusion').addEventListener('click',async e=>{const s=document.querySelector('.answer-card.concise blockquote').textContent;try{await navigator.clipboard.writeText(s);e.target.textContent='Copied';}catch{e.target.textContent='Select and copy the statement above';}});
   navigate('overview');
 }
 document.addEventListener('DOMContentLoaded',setup);
})();
