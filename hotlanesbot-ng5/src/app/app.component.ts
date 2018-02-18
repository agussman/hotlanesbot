import { Component } from '@angular/core';
import { latLng, tileLayer } from 'leaflet';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Hot Lanes Bot';

  options = {
    layers: [
      tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        detectRetina: true
      })
    ],
    zoom: 7,
    center: latLng([ 46.879966, -121.726909 ])
  };

}
